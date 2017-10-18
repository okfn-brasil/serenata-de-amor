module Update exposing (Flags, Msg(..), isValidKeyValue, pair, toTuples, update, updateFromFlags, urlUpdate)

import Dict exposing (Dict)
import Internationalization.Types exposing (Language(..))
import Material
import Model exposing (Model, model)
import Navigation
import Reimbursement.Decoder
import Reimbursement.Search.Update
import Reimbursement.Update
import String


type alias Flags =
    { lang : String
    , googleStreetViewApiKey : String
    }


type Msg
    = ReimbursementMsg Reimbursement.Update.Msg
    | ChangeUrl Navigation.Location
    | LayoutMsg Msg
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ReimbursementMsg msg ->
            let
                updated =
                    Reimbursement.Update.update msg model.reimbursements

                reimbursements =
                    Tuple.first updated

                cmd =
                    Cmd.map ReimbursementMsg <| Tuple.second updated
            in
                ( { model | reimbursements = reimbursements }, cmd )

        ChangeUrl location ->
            urlUpdate location model

        LayoutMsg _ ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateFromFlags : Flags -> Model -> Model
updateFromFlags flags model =
    let
        lang =
            if String.toLower flags.lang == "pt" then
                Portuguese
            else
                English

        googleStreetViewApiKey : Maybe String
        googleStreetViewApiKey =
            Just flags.googleStreetViewApiKey

        newReimbursements =
            Reimbursement.Decoder.updateLanguage lang model.reimbursements
                |> Reimbursement.Decoder.updateGoogleStreetViewApiKey googleStreetViewApiKey

        layout =
            model.layout

        newLayout =
            { layout | lang = lang }
    in
        { model
            | reimbursements = newReimbursements
            , layout = newLayout
            , googleStreetViewApiKey = googleStreetViewApiKey
            , lang = lang
        }


{-| Group a list of strings in a list of string pairs:

    pair ["a", "b", "c", "d", "e"] --> [["a", "b"], ["c", "d"], ["e"]]

-}
pair : List String -> List (List String)
pair query =
    case List.take 2 query of
        [] ->
            []

        keyValue ->
            keyValue :: pair (List.drop 2 query)


{-| Convert a list of lists of strings in a list of key/value tuples:

    toTuples ["foo", "bar"] --> ( "foo", "bar" )

    toTuples ["foo", ""] --> ( "foo", "" )

    toTuples ["", "bar"] --> ( "", "bar" )

    toTuples ["foobar"] --> ( "foobar", "" )

    toTuples ["fo", "ob", "ar"] --> ( "fo", "ob" )

-}
toTuples : List String -> ( String, String )
toTuples query =
    let
        key : String
        key =
            query
                |> List.head
                |> Maybe.withDefault ""

        value : String
        value =
            query
                |> List.drop 1
                |> List.head
                |> Maybe.withDefault ""
    in
        ( key, value )


{-| Filter tuples to make sure they have two strings:

    isValidKeyValue ("foo", "bar") --> True

    isValidKeyValue ("", "bar") --> False

    isValidKeyValue ("foo", "") --> False

    isValidKeyValue ("", "") --> False

-}
isValidKeyValue : ( String, String ) -> Bool
isValidKeyValue ( key, value ) =
    if String.isEmpty key || String.isEmpty value then
        False
    else
        True


{-| Generates a list of URL paramenters (query string) from a URL hash:

   fromHash "#/year/2016/document/42/" --> [ ( "year", "2016" ), ( "documentId", "42" ) ]

-}
fromHash : String -> List ( String, String )
fromHash hash =
    let
        query : Dict String String
        query =
            hash
                |> String.split "/"
                |> List.drop 1
                |> pair
                |> List.map toTuples
                |> List.filter isValidKeyValue
                |> Dict.fromList

        retroCompatibleQuery : Dict String String
        retroCompatibleQuery =
            case Dict.get "document" query of
                Just documentId ->
                    query
                        |> Dict.insert "documentId" documentId
                        |> Dict.remove "document"

                Nothing ->
                    query
    in
        Dict.toList query


urlUpdate : Navigation.Location -> Model -> ( Model, Cmd Msg )
urlUpdate location model =
    let
        query =
            fromHash location.hash

        loading =
            if List.isEmpty query then
                False
            else
                True

        reimbursements =
            if List.isEmpty query then
                Reimbursement.Update.newSearch model.reimbursements
            else
                model.reimbursements

        searchFields =
            Reimbursement.Search.Update.updateFromQuery reimbursements.searchFields query

        results =
            reimbursements.results

        newResults =
            { results | loadingPage = Reimbursement.Decoder.getPage query }

        newReimbursements =
            { reimbursements | searchFields = searchFields, results = newResults, loading = loading }

        cmd =
            Reimbursement.Update.loadReimbursements model.lang model.googleStreetViewApiKey query
    in
        ( { model | reimbursements = newReimbursements }, Cmd.map ReimbursementMsg cmd )
