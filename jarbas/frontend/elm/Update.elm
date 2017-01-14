module Update exposing (Flags, Msg(..), update, urlUpdate, updateFromFlags)

import Reimbursement.Decoder
import Reimbursement.Inputs.Update
import Reimbursement.Update
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Model exposing (Model, model)
import Navigation
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


{-| Generates a list of URL paramenters (query string) from a URL hash:

   >>> fromHash "#/year/2016/document/42/"
   [ ( "year", "2016" ), ( "documentId", "42" ) ]

-}
fromHash : String -> List ( String, String )
fromHash hash =
    let
        indexedList =
            String.split "/" hash |> List.drop 1 |> List.indexedMap (,)

        headersAndValues =
            List.partition (\( i, v ) -> rem i 2 == 0) indexedList

        headers =
            Tuple.first headersAndValues |> List.map (\( i, v ) -> v)

        retroCompatibileHeaders =
            List.map
                (\header ->
                    if header == "document" then
                        "documentId"
                    else
                        header
                )
                headers

        values =
            Tuple.second headersAndValues |> List.map (\( i, v ) -> v)
    in
        List.map2 (,) retroCompatibileHeaders values


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

        inputs =
            Reimbursement.Inputs.Update.updateFromQuery reimbursements.inputs query

        results =
            reimbursements.results

        newResults =
            { results | loadingPage = Reimbursement.Decoder.getPage query }

        newReimbursements =
            { reimbursements | inputs = inputs, results = newResults, loading = loading }

        cmd =
            Reimbursement.Update.loadReimbursements model.lang model.googleStreetViewApiKey query
    in
        ( { model | reimbursements = newReimbursements }, Cmd.map ReimbursementMsg cmd )
