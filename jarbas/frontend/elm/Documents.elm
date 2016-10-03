module Documents exposing (Msg, Model, model, loadDocuments, update, view)

import Documents.Fields as Fields
import Documents.Inputs as Inputs
import Documents.Receipt as Receipt
import Documents.Supplier as Supplier
import Html exposing (a, button, div, form, input, h2, h3, hr, label, table, td, text, th, tr)
import Html.App
import Html.Attributes exposing (class, disabled, for, href, id, type', value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode exposing ((:=), Decoder, int, list, maybe, object2, string)
import Json.Decode.Pipeline exposing (decode, hardcoded, nullable, required)
import Material
import Material.Button as Button
import Material.Grid exposing (grid, cell, size, Device(..))
import Material.Options as Options
import Material.Typography as Typography
import Navigation
import String
import Task


--
-- Model
--


type alias SingleModel =
    { id : Int
    , document_id : Int
    , congressperson_name : String
    , congressperson_id : Int
    , congressperson_document : Int
    , term : Int
    , state : String
    , party : String
    , term_id : Int
    , subquota_number : Int
    , subquota_description : String
    , subquota_group_id : Int
    , subquota_group_description : String
    , supplier : String
    , cnpj_cpf : String
    , document_number : String
    , document_type : Int
    , issue_date : Maybe String
    , document_value : String
    , remark_value : String
    , net_value : String
    , month : Int
    , year : Int
    , installment : Int
    , passenger : String
    , leg_of_the_trip : String
    , batch_number : Int
    , reimbursement_number : Int
    , reimbursement_value : String
    , applicant_id : Int
    , receipt : Receipt.Model
    , supplier_info : Supplier.Model
    }


type alias Results =
    { documents : List SingleModel
    , total : Maybe Int
    }


type alias Model =
    { results : Results
    , inputs : Inputs.Model
    , loading : Bool
    , error : Maybe Http.Error
    , mdl : Material.Model
    }


initialResults : Results
initialResults =
    Results [] Nothing


model : Model
model =
    Model initialResults Inputs.model False Nothing Material.model



--
-- Update
--


type Msg
    = Submit
    | ApiSuccess Results
    | ApiFail Http.Error
    | InputsMsg Inputs.Msg
    | ReceiptMsg Int Receipt.Msg
    | SupplierMsg Int Supplier.Msg
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Submit ->
            let
                url =
                    Inputs.toQuery model.inputs |> toUrl
            in
                ( { model | loading = True }, Navigation.newUrl url )

        ApiSuccess newResults ->
            let
                newModel =
                    { model | results = newResults, loading = False, error = Nothing }

                indexedDocuments =
                    getIndexedDocuments newModel

                indexedSupplierCmds =
                    List.map (\( idx, doc ) -> ( idx, Supplier.load doc.cnpj_cpf )) indexedDocuments

                cmds =
                    List.map (\( idx, cmd ) -> Cmd.map (SupplierMsg idx) cmd) indexedSupplierCmds
            in
                ( newModel, Cmd.batch cmds )

        ApiFail error ->
            ( { model | results = initialResults, error = Just error, loading = False }, Cmd.none )

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

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateSuppliers : Int -> Supplier.Msg -> ( Int, SingleModel ) -> ( SingleModel, Cmd Msg )
updateSuppliers target msg ( index, document ) =
    if target == index then
        let
            updated =
                Supplier.update msg document.supplier_info

            newSupplier =
                fst updated

            newCmd =
                Cmd.map (SupplierMsg target) (snd updated)
        in
            ( { document | supplier_info = newSupplier }, newCmd )
    else
        ( document, Cmd.none )


updateReceipts : Int -> Receipt.Msg -> ( Int, SingleModel ) -> ( SingleModel, Cmd Msg )
updateReceipts target msg ( index, document ) =
    if target == index then
        let
            updated =
                Receipt.update msg document.receipt

            newReceipt =
                fst updated

            newCmd =
                Cmd.map (ReceiptMsg target) (snd updated)
        in
            ( { document | receipt = newReceipt }, newCmd )
    else
        ( document, Cmd.none )


getIndexedDocuments : Model -> List ( Int, SingleModel )
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
       * (Int -> a -> ( Int, SingleModel ) -> ( SingleModel, Cmd Msg )) this is
         a function such as updateSuppliers or updateReceipts
       * (a) The kind of message inside the former argument, i.e. Supplier.Msg
         or Receipt.Msg
-}


getDocumentsAndCmd : Model -> Int -> (Int -> a -> ( Int, SingleModel ) -> ( SingleModel, Cmd Msg )) -> a -> ( Model, Cmd Msg )
getDocumentsAndCmd model index targetUpdate targetMsg =
    let
        results =
            model.results

        indexedDocuments =
            getIndexedDocuments model

        newDocumentsAndCommands =
            List.map (targetUpdate index targetMsg) indexedDocuments

        newDocuments =
            List.map (\( doc, cmd ) -> doc) newDocumentsAndCommands

        newCommands =
            List.map (\( doc, cmd ) -> cmd) newDocumentsAndCommands

        newResults =
            { results | documents = newDocuments }
    in
        ( { model | results = newResults }, Cmd.batch newCommands )


loadDocuments : List ( String, String ) -> Cmd Msg
loadDocuments query =
    let
        url =
            Http.url "/api/document/" query
    in
        Task.perform
            ApiFail
            ApiSuccess
            (Http.get decoder url)


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



--
-- Decoders
--


decoder : Decoder Results
decoder =
    object2 Results
        ("results" := list singleDecoder)
        (maybe ("count" := int))


singleDecoder : Decoder SingleModel
singleDecoder =
    decode SingleModel
        |> required "id" int
        |> required "document_id" int
        |> required "congressperson_name" string
        |> required "congressperson_id" int
        |> required "congressperson_document" int
        |> required "term" int
        |> required "state" string
        |> required "party" string
        |> required "term_id" int
        |> required "subquota_number" int
        |> required "subquota_description" string
        |> required "subquota_group_id" int
        |> required "subquota_group_description" string
        |> required "supplier" string
        |> required "cnpj_cpf" string
        |> required "document_number" string
        |> required "document_type" int
        |> required "issue_date" (nullable string)
        |> required "document_value" string
        |> required "remark_value" string
        |> required "net_value" string
        |> required "month" int
        |> required "year" int
        |> required "installment" int
        |> required "passenger" string
        |> required "leg_of_the_trip" string
        |> required "batch_number" int
        |> required "reimbursement_number" int
        |> required "reimbursement_value" string
        |> required "applicant_id" int
        |> required "receipt" Receipt.decoder
        |> hardcoded Supplier.model



--
-- View
--


viewForm : Model -> Html.Html Msg
viewForm model =
    let
        inputs =
            Inputs.view model.loading model.inputs |> Html.App.map InputsMsg

        action =
            if model.loading then
                "Loading…"
            else
                "Search"

        attr =
            let
                base =
                    [ Button.raised
                    , Button.colored
                    , Button.type' "submit"
                    ]
            in
                if model.loading then
                    base ++ [ Button.disabled ]
                else
                    base

        send =
            grid
                []
                [ cell
                    [ size Desktop 12, size Tablet 8, size Phone 4 ]
                    [ Options.styled
                        div
                        [ Typography.center ]
                        [ Button.render
                            Mdl
                            [ 0 ]
                            model.mdl
                            attr
                            [ text action ]
                        ]
                    ]
                ]
    in
        form [ onSubmit Submit ] [ inputs, send ]


viewError : Maybe Http.Error -> Html.Html Msg
viewError error =
    case error of
        Just _ ->
            h2 [ class "error" ] [ text "Document not found" ]

        Nothing ->
            text ""


viewDocument : Int -> SingleModel -> Html.Html Msg
viewDocument index document =
    let
        labels =
            [ ( "Document ID", toString document.document_id )
            , ( "Congressperson name", document.congressperson_name )
            , ( "Congressperson ID", toString document.congressperson_id )
            , ( "Congressperson document", toString document.congressperson_document )
            , ( "Term", toString document.term )
            , ( "State", document.state )
            , ( "Party", document.party )
            , ( "Term ID", toString document.term_id )
            , ( "Subquota number", toString document.subquota_number )
            , ( "Subquota description", document.subquota_description )
            , ( "Subquota group ID", toString document.subquota_group_id )
            , ( "Subquota group description", document.subquota_group_description )
            , ( "Supplier", document.supplier )
            , ( "CNPJ/CPF", document.cnpj_cpf )
            , ( "Document number", document.document_number )
            , ( "Document type", toString document.document_type )
            , ( "Issue date", Maybe.withDefault "" document.issue_date )
            , ( "Document value", toString document.document_value )
            , ( "Remark value", toString document.remark_value )
            , ( "Net value", toString document.net_value )
            , ( "Month", toString document.month )
            , ( "Year", toString document.year )
            , ( "Installment", toString document.installment )
            , ( "Passenger", document.passenger )
            , ( "Leg of the trip", document.leg_of_the_trip )
            , ( "Batch number", toString document.batch_number )
            , ( "Reimbursement number", toString document.reimbursement_number )
            , ( "Reimbursement value", toString document.reimbursement_value )
            , ( "Applicant ID", toString document.applicant_id )
            ]

        receiptContent =
            Html.App.map (ReceiptMsg index) (Receipt.view document.id document.receipt)

        rows =
            List.append
                (List.map viewDocumentRow labels)
                [ tr
                    []
                    [ th [] [ text "Digitalized receipt" ]
                    , td [] [ receiptContent ]
                    ]
                ]

        title =
            "Document #" ++ (toString document.document_id)
    in
        div
            []
            [ h3 [] [ text title ]
            , table [] rows
            , Html.App.map (SupplierMsg index) (Supplier.view document.supplier_info)
            ]


viewDocuments : Results -> Html.Html Msg
viewDocuments results =
    if List.length results.documents == 0 then
        viewError Nothing
    else
        let
            documents =
                List.indexedMap (\idx doc -> (viewDocument idx doc)) results.documents
                    |> List.intersperse (hr [] [])

            total =
                Maybe.withDefault 0 results.total |> toString

            showing =
                List.length results.documents |> toString

            title =
                if total == showing then
                    h2 [] [ text <| total ++ " documents found." ]
                else
                    h2 [] [ text <| total ++ " documents found. Showing " ++ showing ++ "." ]
        in
            div [] (title :: documents)


viewDocumentRow : ( String, String ) -> Html.Html Msg
viewDocumentRow ( header, content ) =
    tr
        []
        [ th [] [ text header ]
        , td [] [ text content ]
        ]


view : Model -> Html.Html Msg
view model =
    div
        []
        [ viewForm model
        , viewDocuments model.results
        ]
