module Reimbursement.Update exposing (..)

import Array exposing (Array)
import Char
import Format.Url exposing (url)
import Http
import Internationalization.Types exposing (Language(..))
import Material
import Navigation
import Regex exposing (regex, replace)
import Reimbursement.Company.Update as Company
import Reimbursement.Decoder exposing (decoder)
import Reimbursement.Model exposing (Model, Reimbursement, Results, results)
import Reimbursement.Receipt.Model exposing (ReimbursementId)
import Reimbursement.Receipt.Update as Receipt
import Reimbursement.RelatedTable.Update as RelatedTable
import Reimbursement.SameDay.Update as SameDay
import Reimbursement.SameSubquota.Update as SameSubquota
import Reimbursement.Search.Model
import Reimbursement.Search.Update as Search
import String


{-| Give the total page number based on the number of reimbursement found:

    totalPages 3 --> 1

    totalPages 8 --> 2

    totalPages 314 --> 45
-}
totalPages : Int -> Int
totalPages results =
    7.0
        |> (/) (toFloat results)
        |> ceiling


{-| Clean up a numbers only input field:

    onlyDigits "a1b2c3" --> "123"
-}
onlyDigits : String -> String
onlyDigits value =
    String.filter Char.isDigit value


toSameSubquotaFilter : Reimbursement -> SameSubquota.Filter
toSameSubquotaFilter reimbursement =
    SameSubquota.Filter reimbursement.applicantId
        reimbursement.year
        reimbursement.month
        reimbursement.subquotaId


newSearch : Model -> Model
newSearch model =
    { model
        | results = results
        , showForm = True
        , loading = False
        , searchFields = Reimbursement.Search.Model.model
    }


{-| Given a page and the total pages, return if the

    isValidPage 1 42 --> True

    isValidPage 42 42 --> True

    isValidPage 3 42 --> True

    isValidPage 0 42 --> False

    isValidPage 100 42 --> False

-}
isValidPage : Int -> Int -> Bool
isValidPage page total =
    page >= 1 && page <= total


type Msg
    = Submit
    | ToggleForm
    | UpdateJumpTo String
    | RecoverJumpTo
    | Page (Maybe Int)
    | LoadReimbursements (Result Http.Error Results)
    | SearchMsg Search.Msg
    | ReceiptMsg Int Receipt.Msg
    | CompanyMsg Int Company.Msg
    | SameDayMsg Int RelatedTable.Msg
    | SameSubquotaMsg Int RelatedTable.Msg
    | MapMsg
    | TweetMsg
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Submit ->
            let
                url : String
                url =
                    Search.toUrl model.searchFields
                        |> appendUrlHash
            in
                ( { model | loading = True }, Navigation.newUrl url )

        ToggleForm ->
            ( { model | showForm = not model.showForm }, Cmd.none )

        UpdateJumpTo value ->
            value
                |> String.toInt
                |> Result.toMaybe
                |> updateJumpTo model

        RecoverJumpTo ->
            model.results.pageLoaded
                |> Just
                |> updateJumpTo model

        Page (Just page) ->
            let
                total =
                    model.results.total
                        |> Maybe.withDefault 0
                        |> totalPages

                url =
                    appendUrlHash <| "page/" ++ toString page ++ "/" ++ Search.toUrl model.searchFields

                cmd =
                    if isValidPage page total then
                        Navigation.newUrl url
                    else
                        Cmd.none
            in
                ( model, cmd )

        Page Nothing ->
            ( model, Cmd.none )

        LoadReimbursements (Ok results) ->
            let
                showForm : Bool
                showForm =
                    if (Maybe.withDefault 0 results.total) > 0 then
                        False
                    else
                        True

                current : Int
                current =
                    Maybe.withDefault 1 model.results.loadingPage

                newResultsReimbursements : Array Reimbursement
                newResultsReimbursements =
                    Array.map updateRelatedTableParentId results.reimbursements

                newResults : Results
                newResults =
                    { results
                        | reimbursements = newResultsReimbursements
                        , loadingPage = Nothing
                        , pageLoaded = current
                        , jumpTo = Just current
                    }

                newModel : Model
                newModel =
                    { model
                        | results = newResults
                        , showForm = showForm
                        , loading = False
                        , error = Nothing
                    }

                companyCmds : List (Cmd Msg)
                companyCmds =
                    Array.map (.cnpjCpf >> Company.load)
                        newModel.results.reimbursements
                        |> Array.toIndexedList
                        |> List.map (\( idx, cmd ) -> Cmd.map (CompanyMsg idx) cmd)

                sameDayCmds : List (Cmd Msg)
                sameDayCmds =
                    Array.map (.documentId >> SameDay.load)
                        newModel.results.reimbursements
                        |> Array.toIndexedList
                        |> List.map (\( idx, cmd ) -> Cmd.map (SameDayMsg idx) cmd)

                sameSubquotaCmds : List (Cmd Msg)
                sameSubquotaCmds =
                    Array.map (toSameSubquotaFilter >> SameSubquota.load)
                        newModel.results.reimbursements
                        |> Array.toIndexedList
                        |> List.map (\( idx, cmd ) -> Cmd.map (SameSubquotaMsg idx) cmd)

                cmds : List (Cmd Msg)
                cmds =
                    List.concat
                        [ companyCmds
                        , sameDayCmds
                        , sameSubquotaCmds
                        ]
            in
                ( newModel, Cmd.batch cmds )

        LoadReimbursements (Err error) ->
            let
                err =
                    Debug.log "ApiFail" (toString error)
            in
                ( { model | results = results, error = Just error, loading = False }, Cmd.none )

        SearchMsg msg ->
            let
                searchFields =
                    Search.update msg model.searchFields |> Tuple.first
            in
                ( { model | searchFields = searchFields }, Cmd.none )

        CompanyMsg index companyMsg ->
            subModuleUpdate index msg model

        ReceiptMsg index receiptMsg ->
            subModuleUpdate index msg model

        SameDayMsg index sameDayMsg ->
            subModuleUpdate index msg model

        SameSubquotaMsg index sameSubquotaMsg ->
            subModuleUpdate index msg model

        MapMsg ->
            ( model, Cmd.none )

        TweetMsg ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model



--
-- Update helpers
--


subModuleUpdate : Int -> Msg -> Model -> ( Model, Cmd Msg )
subModuleUpdate target msg model =
    case Array.get target model.results.reimbursements of
        Just reimbursement ->
            let
                updated : ( Reimbursement, Cmd Msg )
                updated =
                    getUpdatedSubModule model.lang msg reimbursement

                results : Results
                results =
                    model.results

                newReimbursement : Reimbursement
                newReimbursement =
                    Tuple.first updated

                newReimbursements : Array Reimbursement
                newReimbursements =
                    Array.set target newReimbursement model.results.reimbursements

                newResults : Results
                newResults =
                    { results | reimbursements = newReimbursements }
            in
                ( { model | results = newResults }, Tuple.second updated )

        Nothing ->
            ( model, Cmd.none )


getUpdatedSubModule : Language -> Msg -> Reimbursement -> ( Reimbursement, Cmd Msg )
getUpdatedSubModule lang msg reimbursement =
    case msg of
        CompanyMsg target companyMsg ->
            updateCompany lang target companyMsg reimbursement

        ReceiptMsg target receiptMsg ->
            updateReceipt lang target receiptMsg reimbursement

        SameDayMsg target sameDayMsg ->
            updateSameDay lang target sameDayMsg reimbursement

        SameSubquotaMsg target sameSubquotaMsg ->
            updateSameSubquota lang target sameSubquotaMsg reimbursement

        _ ->
            ( reimbursement, Cmd.none )


updateCompany : Language -> Int -> Company.Msg -> Reimbursement -> ( Reimbursement, Cmd Msg )
updateCompany lang target msg reimbursement =
    reimbursement.supplierInfo
        |> Company.update msg
        |> Tuple.mapFirst (\c -> { c | lang = lang })
        |> Tuple.mapFirst (\c -> { reimbursement | supplierInfo = c })
        |> Tuple.mapSecond (Cmd.map (CompanyMsg target))


updateReceipt : Language -> Int -> Receipt.Msg -> Reimbursement -> ( Reimbursement, Cmd Msg )
updateReceipt lang target msg reimbursement =
    let
        reimbursementId : Maybe ReimbursementId
        reimbursementId =
            ReimbursementId reimbursement.year
                reimbursement.applicantId
                reimbursement.documentId
                |> Just
    in
        reimbursement.receipt
            |> Receipt.update msg
            |> Tuple.mapFirst (\r -> { r | reimbursement = reimbursementId, lang = lang })
            |> Tuple.mapFirst (\r -> { reimbursement | receipt = r })
            |> Tuple.mapSecond (Cmd.map (ReceiptMsg target))


updateSameDay : Language -> Int -> RelatedTable.Msg -> Reimbursement -> ( Reimbursement, Cmd Msg )
updateSameDay lang target msg reimbursement =
    reimbursement.sameDay
        |> RelatedTable.update msg
        |> Tuple.mapFirst (\c -> { c | lang = lang })
        |> Tuple.mapFirst (\c -> { reimbursement | sameDay = c })
        |> Tuple.mapSecond (Cmd.map (SameDayMsg target))


updateSameSubquota : Language -> Int -> RelatedTable.Msg -> Reimbursement -> ( Reimbursement, Cmd Msg )
updateSameSubquota lang target msg reimbursement =
    reimbursement.sameSubquota
        |> RelatedTable.update msg
        |> Tuple.mapFirst (\c -> { c | lang = lang })
        |> Tuple.mapFirst (\c -> { reimbursement | sameSubquota = c })
        |> Tuple.mapSecond (Cmd.map (SameSubquotaMsg target))


updateRelatedTableParentId : Reimbursement -> Reimbursement
updateRelatedTableParentId reimbursement =
    let
        updateModel =
            RelatedTable.updateParentId reimbursement.documentId
    in
        { reimbursement
            | sameDay = updateModel reimbursement.sameDay
            , sameSubquota = updateModel reimbursement.sameSubquota
        }


{-| Convert from camelCase to underscore:

    convertQueryKey "applicationId" --> "application_id"

    convertQueryKey "subquotaGroupId" --> "subquota_group_id"

-}
convertQueryKey : String -> String
convertQueryKey key =
    key
        |> replace Regex.All (regex "[A-Z]") (\{ match } -> "_" ++ match)
        |> String.map Char.toLower


{-| Convert from keys from a query tuple to underscore:

    convertQuery [("applicantId", "1"), ("subqotaGroupId", "2")] --> [("applicant_id", "1"), ("subqota_group_id", "2")]

-}
convertQuery : List ( String, a ) -> List ( String, a )
convertQuery query =
    query
        |> List.map (\( key, value ) -> ( convertQueryKey key, value ))


loadReimbursements : Language -> Maybe String -> List ( String, String ) -> Cmd Msg
loadReimbursements lang apiKey query =
    if List.isEmpty query then
        Cmd.none
    else
        let
            jsonQuery =
                ( "format", "json" ) :: convertQuery query
        in
            Http.get (url "/api/chamber_of_deputies/reimbursement/" jsonQuery)
                (decoder lang apiKey jsonQuery)
                |> Http.send LoadReimbursements


updateJumpTo : Model -> Maybe Int -> ( Model, Cmd Msg )
updateJumpTo model page =
    let
        results : Results
        results =
            model.results
    in
        ( { model | results = { results | jumpTo = page } }, Cmd.none )


appendUrlHash : String -> String
appendUrlHash url =
    if String.isEmpty url then
        ""
    else
        "#/" ++ url
