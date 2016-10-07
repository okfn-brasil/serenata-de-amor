module Documents exposing (Msg, Model, model, loadDocuments, getPage, update, view)

import Char
import Documents.Fields as Fields
import Documents.Inputs as Inputs
import Documents.Map as Map
import Documents.Receipt as Receipt
import Documents.Supplier as Supplier
import Html exposing (a, button, div, form, p, span, text)
import Html.App
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode exposing ((:=), Decoder, int, list, maybe, string)
import Json.Decode.Pipeline exposing (decode, hardcoded, nullable, required)
import Material
import Material.Button as Button
import Material.Color as Color
import Material.Grid exposing (grid, cell, size, Device(..))
import Material.Icon as Icon
import Material.List as List
import Material.Options as Options
import Material.Textfield as Textfield
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
    , previous : Maybe String
    , next : Maybe String
    , loadingPage : Maybe Int
    , pageLoaded : Int
    , jumpTo : String
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
    Results [] Nothing Nothing Nothing Nothing 1 "1"


model : Model
model =
    Model results Inputs.model True False Nothing Material.model



--
-- Update
--


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

        MapMsg ->
            ( model, Cmd.none )

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
        request =
            Http.get
                (decoder query)
                (Http.url "/api/document/" query)
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


getPage : List ( String, String ) -> Maybe Int
getPage query =
    let
        tuple =
            List.head <|
                List.filter
                    (\( name, value ) ->
                        if name == "page" then
                            True
                        else
                            False
                    )
                    query
    in
        case tuple of
            Just ( name, value ) ->
                case String.toInt value of
                    Ok num ->
                        Just num

                    Err e ->
                        Nothing

            Nothing ->
                Nothing



--
-- Decoders
--


decoder : List ( String, String ) -> Decoder Results
decoder query =
    let
        current =
            Maybe.withDefault 1 (getPage query)
    in
        decode Results
            |> required "results" (list singleDecoder)
            |> required "count" (nullable int)
            |> required "previous" (nullable string)
            |> required "next" (nullable string)
            |> hardcoded Nothing
            |> hardcoded current
            |> hardcoded ""


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
-- Form


viewButton : Bool -> Int -> List (Button.Property Msg) -> String -> Html.Html Msg
viewButton loading index defaultAttr defaultLabel =
    let
        label =
            if loading then
                "Loading…"
            else
                defaultLabel

        attr =
            if loading then
                Button.disabled :: defaultAttr
            else
                defaultAttr
    in
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

        viewButton' =
            viewButton model.loading

        send =
            viewButton' 0 [ Button.raised, Button.colored, Button.type' "submit" ] "Search"

        showForm =
            viewButton' 1 [ Button.raised, Button.onClick ToggleForm ] "New search"
    in
        if model.showForm then
            form [ onSubmit Submit ] [ inputs, send ]
        else
            showForm



-- Pagination


jumpToWidth : String -> String
jumpToWidth value =
    let
        actual =
            String.length value |> toFloat

        width =
            if actual <= 1.0 then
                1.618
            else
                actual
    in
        (toString width) ++ "em"


viewJumpTo : Model -> Html.Html Msg
viewJumpTo model =
    let
        cleaned =
            onlyDigits model.results.jumpTo

        input =
            Textfield.render
                Mdl
                [ 0 ]
                model.mdl
                [ Textfield.onInput Update
                , Textfield.value cleaned
                , Options.css "width" (jumpToWidth cleaned)
                , Textfield.style [ (Options.css "text-align" "center") ]
                ]

        page =
            Result.withDefault 0 (String.toInt model.results.jumpTo)

        total =
            Maybe.withDefault 0 model.results.total |> totalPages
    in
        form
            [ onSubmit (Page page) ]
            [ text " Page "
            , input
            , text " of "
            , text (toString total)
            ]


viewPaginationButton : Int -> Int -> String -> Html.Html Msg
viewPaginationButton page index icon =
    div
        []
        [ Button.render
            Mdl
            [ index ]
            model.mdl
            [ Button.minifab
            , Button.onClick <| Page page
            ]
            [ Icon.i icon ]
        ]


viewPagination : Model -> List (Material.Grid.Cell Msg)
viewPagination model =
    let
        current =
            model.results.pageLoaded

        previous =
            case model.results.previous of
                Just url ->
                    viewPaginationButton (current - 1) 1 "chevron_left"

                Nothing ->
                    text ""

        next =
            case model.results.next of
                Just url ->
                    viewPaginationButton (current + 1) 1 "chevron_right"

                Nothing ->
                    text ""
    in
        [ cell
            [ size Desktop 4, size Tablet 2, size Phone 1 ]
            [ Options.styled
                div
                [ Typography.right ]
                [ previous ]
            ]
        , cell
            [ size Desktop 4, size Tablet 4, size Phone 2 ]
            [ Options.styled
                div
                [ Typography.center ]
                [ viewJumpTo model ]
            ]
        , cell
            [ size Desktop 4, size Tablet 2, size Phone 1 ]
            [ Options.styled
                div
                [ Typography.left ]
                [ next ]
            ]
        ]



-- Documents


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

        map =
            Html.App.map (\_ -> MapMsg) <| Map.viewFrom document.supplier_info

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
            [ size Desktop 6, size Tablet 4, size Phone 2 ]
            [ Options.styled
                div
                [ Options.css "margin-top" "3rem", Typography.right ]
                [ receipt, map ]
            ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] (List.map viewDocumentBlock blocks) ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] [ supplierTitle, supplier ] ]
        ]


viewDocuments : Model -> Html.Html Msg
viewDocuments model =
    if List.length model.results.documents == 0 then
        viewError Nothing
    else
        let
            documents =
                List.concat <|
                    List.indexedMap
                        (\idx doc -> (viewDocument idx doc))
                        model.results.documents

            total =
                Maybe.withDefault 1 model.results.total

            title =
                cell
                    [ size Desktop 12, size Tablet 8, size Phone 4 ]
                    [ Options.styled
                        div
                        [ Typography.center, Typography.display1 ]
                        [ (toString total) ++ " documents found." |> text ]
                    ]

            pagination =
                viewPagination model

            cells =
                List.concat
                    [ title :: pagination
                    , documents
                    , pagination
                    ]
        in
            if model.loading then
                text ""
            else
                grid [] cells



--


view : Model -> Html.Html Msg
view model =
    div []
        [ viewForm model
        , viewDocuments model
        ]
