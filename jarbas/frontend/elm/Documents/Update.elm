module Documents.Update exposing (..)

import Char
import Documents.Company.Update as Company
import Documents.Decoder exposing (decoder)
import Documents.Fields as Fields
import Documents.Inputs.Model
import Documents.Inputs.Update as Inputs
import Documents.Model exposing (Model, Document, Results, results)
import Documents.Receipt.Model exposing (ReimbursementId)
import Documents.Receipt.Update as Receipt
import Documents.RelatedTable.Update as RelatedTable
import Documents.SameDay.Update as SameDay
import Documents.SameSubquota.Update as SameSubquota
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
    | LoadDocuments (Result Http.Error Results)
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


toUniqueId : Document -> SameDay.UniqueId
toUniqueId document =
    SameDay.UniqueId document.applicantId document.year document.documentId


toSameSubquotaFilter : Document -> SameSubquota.Filter
toSameSubquotaFilter document =
    SameSubquota.Filter
        document.applicantId
        document.year
        document.month
        document.subquotaId


newSearch : Model -> Model
newSearch model =
    { model
        | results = results
        , showForm = True
        , loading = False
        , inputs = Inputs.updateLanguage model.lang Documents.Inputs.Model.model
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

        LoadDocuments (Ok results) ->
            let
                showForm =
                    if (Maybe.withDefault 0 results.total) > 0 then
                        False
                    else
                        True

                current =
                    Maybe.withDefault 1 model.results.loadingPage

                newResults =
                    { results
                        | loadingPage = Nothing
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

                indexedDocuments =
                    getIndexedDocuments newModel

                indexedCompanyCmds =
                    List.map
                        (\( idx, doc ) -> ( idx, Maybe.withDefault "" doc.cnpjCpf |> Company.load ))
                        indexedDocuments

                indexedSameDayCmds =
                    List.map
                        (\( idx, doc ) -> ( idx, doc |> toUniqueId |> SameDay.load ))
                        indexedDocuments

                indexedSameSubquotaCmds =
                    List.map
                        (\( idx, doc ) -> ( idx, doc |> toSameSubquotaFilter |> SameSubquota.load ))
                        indexedDocuments

                cmds =
                    List.concat
                        [ (List.map (\( idx, cmd ) -> Cmd.map (CompanyMsg idx) cmd) indexedCompanyCmds)
                        , (List.map (\( idx, cmd ) -> Cmd.map (SameDayMsg idx) cmd) indexedSameDayCmds)
                        , (List.map (\( idx, cmd ) -> Cmd.map (SameSubquotaMsg idx) cmd) indexedSameSubquotaCmds)
                        ]
            in
                ( newModel, Cmd.batch cmds )

        LoadDocuments (Err error) ->
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
            getDocumentsAndCmd model index updateReceipts receiptMsg

        CompanyMsg index companyMsg ->
            getDocumentsAndCmd model index updateCompanys companyMsg

        SameDayMsg index sameDayMsg ->
            getDocumentsAndCmd model index updateSameDay sameDayMsg

        SameSubquotaMsg index sameSubquotaMsg ->
            getDocumentsAndCmd model index updateSameSubquota sameSubquotaMsg

        MapMsg ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateCompanys : Language -> Int -> Company.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
updateCompanys lang target msg ( index, document ) =
    if target == index then
        let
            updated =
                Company.update msg document.supplierInfo

            newCompany =
                Tuple.first updated

            newCmd =
                Cmd.map (CompanyMsg target) (Tuple.second updated)
        in
            ( { document | supplierInfo = { newCompany | lang = lang } }, newCmd )
    else
        ( document, Cmd.none )


updateReceipts : Language -> Int -> Receipt.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
updateReceipts lang target msg ( index, document ) =
    if target == index then
        let
            updated =
                Receipt.update msg document.receipt

            updatedReceipt =
                Tuple.first updated

            newCmd =
                Tuple.second updated |> Cmd.map (ReceiptMsg target)

            reimbursement =
                ReimbursementId document.year document.applicantId document.documentId

            newReceipt =
                { updatedReceipt
                    | lang = lang
                    , reimbursement = Just reimbursement
                }
        in
            ( { document | receipt = newReceipt }, newCmd )
    else
        ( document, Cmd.none )


updateSameDay : Language -> Int -> RelatedTable.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
updateSameDay lang target msg ( index, document ) =
    if target == index then
        let
            updated =
                RelatedTable.update msg document.sameDay

            sameDay =
                Tuple.first updated

            newSameDay =
                { sameDay | lang = lang }

            cmd =
                Tuple.second updated |> Cmd.map (SameDayMsg target)
        in
            ( { document | sameDay = newSameDay }, cmd )
    else
        ( document, Cmd.none )


updateSameSubquota : Language -> Int -> RelatedTable.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
updateSameSubquota lang target msg ( index, document ) =
    if target == index then
        let
            updated =
                RelatedTable.update msg document.sameSubquota

            sameSubquota =
                Tuple.first updated

            newSameSubquota =
                { sameSubquota | lang = lang }

            cmd =
                Tuple.second updated |> Cmd.map (SameSubquotaMsg target)
        in
            ( { document | sameSubquota = newSameSubquota }, cmd )
    else
        ( document, Cmd.none )


getIndexedDocuments : Model -> List ( Int, Document )
getIndexedDocuments model =
    let
        results =
            model.results

        documents =
            results.documents
    in
        List.indexedMap (,) results.documents



{-
   This type signature is terrible, but it is a flexible function to update
   Companys and Receipts.

   It returns a new model with the documents field updated, and the list of
   commands already mapped to the current module (i.e.  it returns what the
   general update function is expecting).

   The arguments it expects:
       * (Model) current model
       * (Int) index of the object (Company or Receipt) being updated
       * (Int -> a -> ( Int, Document ) -> ( Document, Cmd Msg )) this is
         a function such as updateCompanys or updateReceipts
       * (a) The kind of message inside the former argument, i.e. Company.Msg
         or Receipt.Msg
-}


getDocumentsAndCmd : Model -> Int -> (Language -> Int -> a -> ( Int, Document ) -> ( Document, Cmd Msg )) -> a -> ( Model, Cmd Msg )
getDocumentsAndCmd model index targetUpdate targetMsg =
    let
        results =
            model.results

        indexedDocuments =
            getIndexedDocuments model

        newDocumentsAndCommands =
            List.map (targetUpdate model.lang index targetMsg) indexedDocuments

        newDocuments =
            List.map (\( doc, cmd ) -> doc) newDocumentsAndCommands

        newCommands =
            List.map (\( doc, cmd ) -> cmd) newDocumentsAndCommands

        newResults =
            { results | documents = newDocuments }
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


loadDocuments : Language -> String -> List ( String, String ) -> Cmd Msg
loadDocuments lang apiKey query =
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
                |> Http.send LoadDocuments


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
