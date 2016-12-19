module Documents.Update exposing (..)

import Char
import Documents.Fields as Fields
import Documents.Inputs.Update as Inputs
import Documents.Inputs.Model
import Documents.Receipt.Model exposing (ReimbursementId)
import Documents.Receipt.Update as Receipt
import Documents.Decoder exposing (decoder)
import Documents.Model exposing (Model, Document, Results, results)
import Documents.Supplier.Update as Supplier
import Http
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Navigation
import Regex exposing (regex, replace)
import String
import Task


totalPages : Int -> Int
totalPages results =
    toFloat results / 7.0 |> ceiling


onlyDigits : String -> String
onlyDigits value =
    String.filter (\c -> Char.isDigit c) value


type Msg
    = Submit
    | ToggleForm
    | Update String
    | Page Int
    | ApiSuccess Results
    | ApiFail Http.Error
    | InputsMsg Inputs.Msg
    | ReceiptMsg Int Receipt.Msg
    | SupplierMsg Int Supplier.Msg
    | MapMsg
    | Mdl (Material.Msg Msg)


newSearch : Model -> Model
newSearch model =
    { model
        | results = results
        , showForm = True
        , loading = False
        , inputs = Documents.Inputs.Model.model
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
                    if List.member page [1..total] then
                        Navigation.newUrl (toUrl query)
                    else
                        Cmd.none
            in
                ( model, cmd )

        ApiSuccess results ->
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

                indexedSupplierCmds =
                    List.map (\( idx, doc ) -> ( idx, Maybe.withDefault "" doc.cnpjCpf |> Supplier.load )) indexedDocuments

                cmds =
                    List.map (\( idx, cmd ) -> Cmd.map (SupplierMsg idx) cmd) indexedSupplierCmds
            in
                ( newModel, Cmd.batch cmds )

        ApiFail error ->
            let
                err =
                    Debug.log (toString error)
            in
                ( { model | results = results, error = Just error, loading = False }, Cmd.none )

        InputsMsg msg ->
            let
                inputs =
                    Inputs.update msg model.inputs |> fst
            in
                ( { model | inputs = inputs }, Cmd.none )

        ReceiptMsg index receiptMsg ->
            getDocumentsAndCmd model index updateReceipts receiptMsg

        SupplierMsg index supplierMsg ->
            getDocumentsAndCmd model index updateSuppliers supplierMsg

        MapMsg ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateSuppliers : Language -> Int -> Supplier.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
updateSuppliers lang target msg ( index, document ) =
    if target == index then
        let
            updated =
                Supplier.update msg document.supplierInfo

            newSupplier =
                fst updated

            newCmd =
                Cmd.map (SupplierMsg target) (snd updated)
        in
            ( { document | supplierInfo = { newSupplier | lang = lang } }, newCmd )
    else
        ( document, Cmd.none )


updateReceipts : Language -> Int -> Receipt.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
updateReceipts lang target msg ( index, document ) =
    if target == index then
        let
            updated =
                Receipt.update msg document.receipt

            updatedReceipt =
                fst updated

            newCmd =
                snd updated |> Cmd.map (ReceiptMsg target)

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
   Suppliers and Receipts.

   It returns a new model with the documents field updated, and the list of
   commands already mapped to the current module (i.e.  it returns what the
   general update function is expecting).

   The arguments it expects:
       * (Model) current model
       * (Int) index of the object (Supplier or Receipt) being updated
       * (Int -> a -> ( Int, Document ) -> ( Document, Cmd Msg )) this is
         a function such as updateSuppliers or updateReceipts
       * (a) The kind of message inside the former argument, i.e. Supplier.Msg
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

            request =
                Http.get
                    (decoder lang apiKey jsonQuery)
                    (Http.url "/api/reimbursement/" jsonQuery)
        in
            Task.perform
                ApiFail
                ApiSuccess
                request


toUrl : List ( String, String ) -> String
toUrl query =
    let
        validQueries =
            List.filter Fields.isSearchable query

        pairs =
            List.map (\( index, value ) -> index ++ "/" ++ value) validQueries

        trailing =
            String.join "/" pairs
    in
        if List.isEmpty validQueries then
            ""
        else
            "#/" ++ trailing
