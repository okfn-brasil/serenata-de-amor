module Documents exposing (Msg, Model, model, loadDocuments, update, view)

import Documents.Fields as Fields
import Documents.Inputs as Inputs
import Documents.Receipt as Receipt
import Documents.Supplier as Supplier
import Html exposing (a, button, div, form, p, span, text)
import Html.App
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode exposing ((:=), Decoder, int, list, maybe, object2, string)
import Json.Decode.Pipeline exposing (decode, hardcoded, nullable, required)
import Material
import Material.Button as Button
import Material.Color as Color
import Material.Grid exposing (grid, cell, size, Device(..))
import Material.Icon as Icon
import Material.List as List
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
    , showForm : Bool
    , loading : Bool
    , error : Maybe Http.Error
    , mdl : Material.Model
    }


results : Results
results =
    Results [] Nothing


model : Model
model =
    Model results Inputs.model True False Nothing Material.model



--
-- Update
--


type Msg
    = Submit
    | ToggleForm
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

        ToggleForm ->
            ( { model | showForm = not model.showForm }, Cmd.none )

        ApiSuccess newResults ->
            let
                showForm =
                    if (Maybe.withDefault 0 newResults.total) > 0 then
                        False
                    else
                        True

                newModel =
                    { model | results = newResults, showForm = showForm, loading = False, error = Nothing }

                indexedDocuments =
                    getIndexedDocuments newModel

                indexedSupplierCmds =
                    List.map (\( idx, doc ) -> ( idx, Supplier.load doc.cnpj_cpf )) indexedDocuments

                cmds =
                    List.map (\( idx, cmd ) -> Cmd.map (SupplierMsg idx) cmd) indexedSupplierCmds
            in
                ( newModel, Cmd.batch cmds )

        ApiFail error ->
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


centeredButton : Int -> List (Button.Property Msg) -> String -> Html.Html Msg
centeredButton index attr label =
    grid
        []
        [ cell
            [ size Desktop 12, size Tablet 8, size Phone 4 ]
            [ Options.styled
                div
                [ Typography.center ]
                [ Button.render
                    Mdl
                    [ index ]
                    model.mdl
                    attr
                    [ text label ]
                ]
            ]
        ]


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

        sendAttr =
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

        sendButton =
            centeredButton 0 sendAttr action

        showFormButton =
            centeredButton 1 [ Button.raised, Button.onClick ToggleForm ] "New search"
    in
        if model.showForm then
            form [ onSubmit Submit ] [ inputs, sendButton ]
        else
            showFormButton


viewError : Maybe Http.Error -> Html.Html Msg
viewError error =
    case error of
        Just _ ->
            Options.styled p [ Typography.title ] [ text "Document not found" ]

        Nothing ->
            text ""


viewDocumentBlockLine : ( String, String ) -> Html.Html Msg
viewDocumentBlockLine ( label, value ) =
    let
        styles =
            [ Options.css "display" "flex"
            , Options.css "justify-content" "space-between"
            , Options.css "align-items" "center"
            ]

        labelStyles =
            Options.css "width" "30%" :: styles
    in
        Options.styled div
            [ Options.css "display" "flex"
            , Options.css "flex-direction" "row"
            ]
            [ Options.styled span (Typography.body2 :: labelStyles) [ text label ]
            , Options.styled span (Typography.body1 :: styles) [ text value ]
            ]


viewDocumentBlock : ( String, String, List ( String, String ) ) -> Html.Html Msg
viewDocumentBlock ( title, icon, fields ) =
    let
        iconTag =
            Icon.view icon [ Options.css "transform" "translateY(0.4rem)" ]
        ps =
            if title == "Supplier info" then
                Options.styled
                    p
                    [ Typography.caption ]
                    [ text """If we can find the CNPJ of this supplier in our
                    database more info will be available in the sidebar.""" ]
            else
                text ""
    in
        div
            []
            [ Options.styled
                p
                [ Typography.subhead ]
                [ iconTag, text (" " ++ title) ]
            , List.ul [] (List.map viewDocumentBlockLine fields)
            , ps
            ]


viewDocument : Int -> SingleModel -> List (Material.Grid.Cell Msg)
viewDocument index document =
    let
        blocks =
            [ ( "Congressperson details"
              , "face"
              , [ ( "Name", document.congressperson_name )
                , ( "ID", toString document.congressperson_id )
                , ( "Document", toString document.congressperson_document )
                , ( "State", document.state )
                , ( "Party", document.party )
                , ( "Term", toString document.term )
                , ( "Term ID", toString document.term_id )
                ]
              )
            , ( "Subquota details"
              , "list"
              , [ ( "Number", toString document.subquota_number )
                , ( "Description", document.subquota_description )
                , ( "Group ID", toString document.subquota_group_id )
                , ( "Group description", document.subquota_group_description )
                ]
              )
            , ( "Supplier info"
              , "store"
              , [ ( "Name", document.supplier )
                , ( "CNPJ/CPF", document.cnpj_cpf )
                ]
              )
            , ( "Document details"
              , "receipt"
              , [ ( "ID", toString document.document_id )
                , ( "Number", document.document_number )
                , ( "Type", toString document.document_type )
                , ( "Month", toString document.month )
                , ( "Year", toString document.year )
                , ( "Issue date", Maybe.withDefault "" document.issue_date )
                ]
              )
            , ( "Values"
              , "monetization_on"
              , [ ( "Document", toString document.document_value )
                , ( "Remark", toString document.remark_value )
                , ( "Net", toString document.net_value )
                , ( "Reimbursement", toString document.reimbursement_value )
                , ( "Installment", toString document.installment )
                ]
              )
            , ( "Trip details"
              , "flight"
              , [ ( "Passenger", document.passenger )
                , ( "Leg", document.leg_of_the_trip )
                ]
              )
            , ( "Application details"
              , "folder"
              , [ ( "Applicant ID", toString document.applicant_id )
                , ( "Batch number", toString document.batch_number )
                , ( "Reimbursement number", toString document.reimbursement_number )
                ]
              )
            ]

        receipt =
            Html.App.map (ReceiptMsg index) (Receipt.view document.id document.receipt)

        title =
            Options.styled
                p
                [ Typography.headline, Color.text Color.primary ]
                [ "Document #" ++ (toString document.document_id) |> text ]

        supplier =
            Html.App.map (SupplierMsg index) (Supplier.view document.supplier_info)

        supplierTitle =
            Options.styled
                p
                [ Typography.headline ]
                [ text "" ]
    in
        [ cell
            [ size Desktop 6, size Tablet 4, size Phone 2 ]
            [ Options.styled div [ Options.css "margin-top" "3rem" ] [ title ] ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] (List.map viewDocumentBlock blocks) ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] [ supplierTitle, supplier ] ]
        ]


viewDocuments : Results -> Html.Html Msg
viewDocuments results =
    if List.length results.documents == 0 then
        viewError Nothing
    else
        let
            documents =
                List.concat <|
                    List.indexedMap
                        (\idx doc -> (viewDocument idx doc))
                        results.documents

            total =
                Maybe.withDefault 0 results.total |> toString

            showing =
                List.length results.documents |> toString

            title =
                if total == showing then
                    total ++ " documents found."
                else
                    total ++ " documents found. Showing " ++ showing ++ "."

            titleCell =
                cell
                    [ size Desktop 12, size Tablet 8, size Phone 4 ]
                    [ Options.styled
                        div
                        [ Typography.center, Typography.display1 ]
                        [ text title ]
                    ]
        in
            grid [] (titleCell :: documents)


view : Model -> Html.Html Msg
view model =
    div
        []
        [ viewForm model
        , viewDocuments model.results
        ]
