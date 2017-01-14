module Reimbursement.Update exposing (..)

import Char
import Reimbursement.Company.Update as Company
import Reimbursement.Decoder exposing (decoder)
import Reimbursement.Fields as Fields
import Reimbursement.Inputs.Model
import Reimbursement.Inputs.Update as Inputs
import Reimbursement.Model exposing (Model, Reimbursement, Results, results)
import Reimbursement.Receipt.Model exposing (ReimbursementId)
import Reimbursement.Receipt.Update as Receipt
import Reimbursement.RelatedTable.Update as RelatedTable
import Reimbursement.SameDay.Update as SameDay
import Reimbursement.SameSubquota.Update as SameSubquota
import Format.Url exposing (url)
import Http
import Internationalization exposing (Language)
import Material
import Navigation
import Regex exposing (regex, replace)
import String


type Msg
    = Submit
    | ToggleForm
    | Update String
    | Page Int
    | LoadReimbursements (Result Http.Error Results)
    | InputsMsg Inputs.Msg
    | ReceiptMsg Int Receipt.Msg
    | CompanyMsg Int Company.Msg
    | SameDayMsg Int RelatedTable.Msg
    | SameSubquotaMsg Int RelatedTable.Msg
    | MapMsg
    | Mdl (Material.Msg Msg)


{-| Give the total page number based on the number of reimbursement found:

    >>> totalPages 3
    1

    >>> totalPages 8
    2

    >>> totalPages 314
    45
-}
totalPages : Int -> Int
totalPages results =
    toFloat results / 7.0 |> ceiling


{-| Clean up a numbers only input field:

    >>> onlyDigits "a1b2c3"
    "123"
-}
onlyDigits : String -> String
onlyDigits value =
    String.filter (\c -> Char.isDigit c) value


toUniqueId : Reimbursement -> SameDay.UniqueId
toUniqueId reimbursement =
    SameDay.UniqueId reimbursement.applicantId reimbursement.year reimbursement.documentId


toSameSubquotaFilter : Reimbursement -> SameSubquota.Filter
toSameSubquotaFilter reimbursement =
    SameSubquota.Filter
        reimbursement.applicantId
        reimbursement.year
        reimbursement.month
        reimbursement.subquotaId


newSearch : Model -> Model
newSearch model =
    { model
        | results = results
        , showForm = True
        , loading = False
        , inputs = Inputs.updateLanguage model.lang Reimbursement.Inputs.Model.model
    }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Submit ->
            let
                url =
                    toUrl (Inputs.toQuery model.inputs)
            in
                ( { model | loading = True }, Navigation.newUrl url )

        ToggleForm ->
            ( { model | showForm = not model.showForm }, Cmd.none )

        Update value ->
            let
                results =
                    model.results

                newResults =
                    { results | jumpTo = onlyDigits value }
            in
                ( { model | results = newResults }, Cmd.none )

        Page page ->
            let
                total =
                    Maybe.withDefault 0 model.results.total |> totalPages

                query =
                    ( "page", toString page ) :: Inputs.toQuery model.inputs

                cmd =
                    if List.member page (List.range 1 total) then
                        Navigation.newUrl (toUrl query)
                    else
                        Cmd.none
            in
                ( model, cmd )

        LoadReimbursements (Ok results) ->
            let
                showForm =
                    if (Maybe.withDefault 0 results.total) > 0 then
                        False
                    else
                        True

                current =
                    Maybe.withDefault 1 model.results.loadingPage

                newResultReimbursements =
                    List.map updateRelatedTableParentId results.reimbursements

                newResults =
                    { results
                        | reimbursements = newResultReimbursements
                        , loadingPage = Nothing
                        , pageLoaded = current
                        , jumpTo = toString current
                    }

                newModel =
                    { model
                        | results = newResults
                        , showForm = showForm
                        , loading = False
                        , error = Nothing
                    }

                indexedReimbursements =
                    getIndexedReimbursements newModel

                indexedCompanyCmds =
                    List.map
                        (\( idx, doc ) -> ( idx, Maybe.withDefault "" doc.cnpjCpf |> Company.load ))
                        indexedReimbursements

                indexedSameDayCmds =
                    List.map
                        (\( idx, doc ) -> ( idx, doc |> toUniqueId |> SameDay.load ))
                        indexedReimbursements

                indexedSameSubquotaCmds =
                    List.map
                        (\( idx, doc ) -> ( idx, doc |> toSameSubquotaFilter |> SameSubquota.load ))
                        indexedReimbursements

                cmds =
                    List.concat
                        [ (List.map (\( idx, cmd ) -> Cmd.map (CompanyMsg idx) cmd) indexedCompanyCmds)
                        , (List.map (\( idx, cmd ) -> Cmd.map (SameDayMsg idx) cmd) indexedSameDayCmds)
                        , (List.map (\( idx, cmd ) -> Cmd.map (SameSubquotaMsg idx) cmd) indexedSameSubquotaCmds)
                        ]
            in
                ( newModel, Cmd.batch cmds )

        LoadReimbursements (Err error) ->
            let
                err =
                    Debug.log "ApiFail" (toString error)
            in
                ( { model | results = results, error = Just error, loading = False }, Cmd.none )

        InputsMsg msg ->
            let
                inputs =
                    Inputs.update msg model.inputs |> Tuple.first
            in
                ( { model | inputs = inputs }, Cmd.none )

        ReceiptMsg index receiptMsg ->
            getReimbursementsAndCmd model index updateReceipts receiptMsg

        CompanyMsg index companyMsg ->
            getReimbursementsAndCmd model index updateCompanys companyMsg

        SameDayMsg index sameDayMsg ->
            getReimbursementsAndCmd model index updateSameDay sameDayMsg

        SameSubquotaMsg index sameSubquotaMsg ->
            getReimbursementsAndCmd model index updateSameSubquota sameSubquotaMsg

        MapMsg ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateCompanys : Language -> Int -> Company.Msg -> ( Int, Reimbursement ) -> ( Reimbursement, Cmd Msg )
updateCompanys lang target msg ( index, reimbursement ) =
    if target == index then
        let
            updated =
                Company.update msg reimbursement.supplierInfo

            newCompany =
                Tuple.first updated

            newCmd =
                Cmd.map (CompanyMsg target) (Tuple.second updated)
        in
            ( { reimbursement | supplierInfo = { newCompany | lang = lang } }, newCmd )
    else
        ( reimbursement, Cmd.none )


updateReceipts : Language -> Int -> Receipt.Msg -> ( Int, Reimbursement ) -> ( Reimbursement, Cmd Msg )
updateReceipts lang target msg ( index, reimbursement ) =
    if target == index then
        let
            updated =
                Receipt.update msg reimbursement.receipt

            updatedReceipt =
                Tuple.first updated

            newCmd =
                Tuple.second updated |> Cmd.map (ReceiptMsg target)

            reimbursementId =
                ReimbursementId
                    reimbursement.year
                    reimbursement.applicantId
                    reimbursement.documentId

            newReceipt =
                { updatedReceipt
                    | lang = lang
                    , reimbursement = Just reimbursementId
                }
        in
            ( { reimbursement | receipt = newReceipt }, newCmd )
    else
        ( reimbursement, Cmd.none )


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


updateSameDay : Language -> Int -> RelatedTable.Msg -> ( Int, Reimbursement ) -> ( Reimbursement, Cmd Msg )
updateSameDay lang target msg ( index, reimbursement ) =
    if target == index then
        let
            updated =
                RelatedTable.update msg reimbursement.sameDay

            sameDay =
                Tuple.first updated

            newSameDay =
                { sameDay | lang = lang }

            cmd =
                Tuple.second updated |> Cmd.map (SameDayMsg target)
        in
            ( { reimbursement | sameDay = newSameDay }, cmd )
    else
        ( reimbursement, Cmd.none )


updateSameSubquota : Language -> Int -> RelatedTable.Msg -> ( Int, Reimbursement ) -> ( Reimbursement, Cmd Msg )
updateSameSubquota lang target msg ( index, reimbursement ) =
    if target == index then
        let
            updated =
                RelatedTable.update msg reimbursement.sameSubquota

            sameSubquota =
                Tuple.first updated

            newSameSubquota =
                { sameSubquota | lang = lang }

            cmd =
                Tuple.second updated |> Cmd.map (SameSubquotaMsg target)
        in
            ( { reimbursement | sameSubquota = newSameSubquota }, cmd )
    else
        ( reimbursement, Cmd.none )


getIndexedReimbursements : Model -> List ( Int, Reimbursement )
getIndexedReimbursements model =
    let
        results =
            model.results

        reimbursements =
            results.reimbursements
    in
        List.indexedMap (,) results.reimbursements



{-
   This type signature is terrible, but it is a flexible function to update
   Companys and Receipts.

   It returns a new model with the reimbursements field updated, and the list of
   commands already mapped to the current module (i.e.  it returns what the
   general update function is expecting).

   The arguments it expects:
       * (Model) current model
       * (Int) index of the object (Company or Receipt) being updated
       * (Int -> a -> ( Int, Reimbursement ) -> ( Reimbursement, Cmd Msg )) this is
         a function such as updateCompanys or updateReceipts
       * (a) The kind of message inside the former argument, i.e. Company.Msg
         or Receipt.Msg
-}


getReimbursementsAndCmd : Model -> Int -> (Language -> Int -> a -> ( Int, Reimbursement ) -> ( Reimbursement, Cmd Msg )) -> a -> ( Model, Cmd Msg )
getReimbursementsAndCmd model index targetUpdate targetMsg =
    let
        results =
            model.results

        indexedReimbursements =
            getIndexedReimbursements model

        newReimbursementsAndCommands =
            List.map (targetUpdate model.lang index targetMsg) indexedReimbursements

        newReimbursements =
            List.map Tuple.first newReimbursementsAndCommands

        newCommands =
            List.map Tuple.second newReimbursementsAndCommands

        newResults =
            { results | reimbursements = newReimbursements }
    in
        ( { model | results = newResults }, Cmd.batch newCommands )


{-| Convert from camelCase to underscore:

    >>> convertQueryKey "applicationId"
    "application_id"

    >>> convertQueryKey "subquotaGroupId"
    "subquota_group_id"

-}
convertQueryKey : String -> String
convertQueryKey key =
    key
        |> replace Regex.All (regex "[A-Z]") (\{ match } -> "_" ++ match)
        |> String.map Char.toLower


{-| Convert from keys from a query tuple to underscore:

    >>> convertQuery [("applicantId", "1"), ("subqotaGroupId", "2")]
    [("applicant_id", "1"), ("subqota_group_id", "2")]

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
            Http.get
                (url "/api/reimbursement/" jsonQuery)
                (decoder lang apiKey jsonQuery)
                |> Http.send LoadReimbursements


{-| Convert a list of key/value query pairs to a valid URL:

    >>> toUrl [ ( "year", "2016" ), ( "foo", "bar" ) ]
    "#/year/2016"

    >>> toUrl [ ( "foo", "bar" ) ]
    ""

-}
toUrl : List ( String, String ) -> String
toUrl query =
    let
        validQueries =
            List.filter Fields.isSearchable query
    in
        if List.isEmpty validQueries then
            ""
        else
            validQueries
                |> List.map (\( index, value ) -> index ++ "/" ++ value)
                |> String.join "/"
                |> (++) "#/"
