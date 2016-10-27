module Documents exposing (..)

import Char
import Documents.Fields as Fields
import Documents.Inputs as Inputs
import Documents.Map as Map
import Documents.Receipt as Receipt
import Documents.Supplier as Supplier
import Html exposing (div, form, p, span, text)
import Html.App
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Internationalization exposing (Language(..), TranslationId(..), translate)
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


type alias Document =
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
    { documents : List Document
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
    , lang : Language
    , mdl : Material.Model
    }


results : Results
results =
    Results [] Nothing Nothing Nothing Nothing 1 "1"


model : Model
model =
    Model results Inputs.model True False Nothing English Material.model



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
            let
                err =
                    Debug.crash (toString error)
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


updateSuppliers : Int -> Supplier.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
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


updateReceipts : Int -> Receipt.Msg -> ( Int, Document ) -> ( Document, Cmd Msg )
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


getDocumentsAndCmd : Model -> Int -> (Int -> a -> ( Int, Document ) -> ( Document, Cmd Msg )) -> a -> ( Model, Cmd Msg )
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
    if List.isEmpty query then
        Cmd.none
    else
        let
            jsonQuery =
                ( "format", "json" ) :: query

            request =
                Http.get
                    (decoder jsonQuery)
                    (Http.url "/api/document/" jsonQuery)
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


singleDecoder : Decoder Document
singleDecoder =
    decode Document
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


updateDocumentLanguage : Language -> Document -> Document
updateDocumentLanguage lang document =
    let
        receipt =
            document.receipt

        newReceipt =
            { receipt | lang = lang }

        supplier =
            document.supplier_info

        newSupplier =
            { supplier | lang = lang }
    in
        { document | receipt = newReceipt, supplier_info = newSupplier }


updateLanguage : Language -> Model -> Model
updateLanguage lang model =
    let
        results =
            model.results

        newDocuments =
            List.map (updateDocumentLanguage lang) model.results.documents

        newResults =
            { results | documents = newDocuments }

        newInputs =
            Inputs.updateLanguage lang model.inputs
    in
        { model | lang = lang, inputs = newInputs, results = newResults }



--
-- View
--
-- Form


viewButton : Model -> Int -> List (Button.Property Msg) -> TranslationId -> Html.Html Msg
viewButton model index defaultAttr defaultLabel =
    let
        label =
            if model.loading then
                translate model.lang Loading
            else
                translate model.lang defaultLabel

        attr =
            if model.loading then
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

        send =
            viewButton
                model
                0
                [ Button.raised, Button.colored, Button.type' "submit" ]
                Search

        showForm =
            viewButton
                model
                1
                [ Button.raised, Button.onClick ToggleForm ]
                NewSearch
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
            [ text (translate model.lang PaginationPage)
            , input
            , text (translate model.lang PaginationOf)
            , text (toString total)
            ]


viewPaginationButton : Model -> Int -> Int -> String -> Html.Html Msg
viewPaginationButton model page index icon =
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

        total =
            Maybe.withDefault 0 model.results.total |> totalPages

        previous =
            case model.results.previous of
                Just url ->
                    viewPaginationButton model (current - 1) 1 "chevron_left"

                Nothing ->
                    text ""

        next =
            case model.results.next of
                Just url ->
                    viewPaginationButton model (current + 1) 2 "chevron_right"

                Nothing ->
                    text ""
    in
        if current >= total then
            []
        else
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


viewError : Language -> Maybe Http.Error -> Html.Html Msg
viewError lang error =
    case error of
        Just _ ->
            Options.styled
                p
                [ Typography.title ]
                [ text (translate lang DocumentNotFound) ]

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


viewDocumentBlock : Language -> ( String, String, List ( String, String ) ) -> Html.Html Msg
viewDocumentBlock lang ( title, icon, fields ) =
    let
        iconTag =
            Icon.view icon [ Options.css "transform" "translateY(0.4rem)" ]

        ps =
            if title == (translate lang FieldsetSupplier) then
                Options.styled
                    p
                    [ Typography.caption ]
                    [ text (translate lang FieldsetSupplierDetails) ]
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


viewDocument : Language -> Int -> Document -> List (Material.Grid.Cell Msg)
viewDocument lang index document =
    let
        getLabel =
            Fields.getLabel lang

        blocks =
            [ ( translate lang FieldsetCongressperson
              , "face"
              , [ ( getLabel "congressperson_name", document.congressperson_name )
                , ( getLabel "congressperson_id", toString document.congressperson_id )
                , ( getLabel "congressperson_document", toString document.congressperson_document )
                , ( getLabel "state", document.state )
                , ( getLabel "party", document.party )
                , ( getLabel "term", toString document.term )
                , ( getLabel "term_id", toString document.term_id )
                ]
              )
            , ( translate lang FieldsetSubquota
              , "list"
              , [ ( getLabel "subquota_number", toString document.subquota_number )
                , ( getLabel "subquota_description", document.subquota_description )
                , ( getLabel "subquota_group_id", toString document.subquota_group_id )
                , ( getLabel "subquota_group_description", document.subquota_group_description )
                ]
              )
            , ( translate lang FieldsetSupplier
              , "store"
              , [ ( getLabel "supplier", document.supplier )
                , ( getLabel "cnpj_cpf", document.cnpj_cpf )
                ]
              )
            , ( translate lang FieldsetDocument
              , "receipt"
              , [ ( getLabel "document_id", toString document.document_id )
                , ( getLabel "document_number", document.document_number )
                , ( getLabel "document_type", toString document.document_type )
                , ( getLabel "month", toString document.month )
                , ( getLabel "year", toString document.year )
                , ( getLabel "issue_date", Maybe.withDefault "" document.issue_date )
                ]
              )
            , ( translate lang FieldsetValues
              , "monetization_on"
              , [ ( getLabel "document_value", toString document.document_value )
                , ( getLabel "remark_value", toString document.remark_value )
                , ( getLabel "net_value", toString document.net_value )
                , ( getLabel "reimbursement_value", toString document.reimbursement_value )
                , ( getLabel "installment", toString document.installment )
                ]
              )
            , ( translate lang FieldsetTrip
              , "flight"
              , [ ( getLabel "passenger", document.passenger )
                , ( getLabel "leg_of_the_trip", document.leg_of_the_trip )
                ]
              )
            , ( translate lang FieldsetApplication
              , "folder"
              , [ ( getLabel "applicant_id", toString document.applicant_id )
                , ( getLabel "batch_number", toString document.batch_number )
                , ( getLabel "reimbursement_number", toString document.reimbursement_number )
                ]
              )
            ]

        receipt =
            Html.App.map (ReceiptMsg index) (Receipt.view document.id document.receipt)

        map =
            Html.App.map (\_ -> MapMsg) <| Map.viewFrom lang document.supplier_info

        title =
            Options.styled
                p
                [ Typography.headline, Color.text Color.primary ]
                [ (translate lang DocumentTitle) ++ (toString document.document_id) |> text ]

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
            [ Options.styled div [] (List.map (viewDocumentBlock lang) blocks) ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] [ supplierTitle, supplier ] ]
        ]


viewDocuments : Model -> Html.Html Msg
viewDocuments model =
    let
        documents =
            List.concat <|
                List.indexedMap
                    (\idx doc -> (viewDocument model.lang idx doc))
                    model.results.documents

        total =
            Maybe.withDefault 0 model.results.total

        searched =
            Inputs.toQuery model.inputs |> List.isEmpty |> not

        results =
            if total == 1 then
                (translate model.lang ResultTitleSingular)
            else
                (translate model.lang ResultTitlePlural)

        title =
            cell
                [ size Desktop 12, size Tablet 8, size Phone 4 ]
                [ Options.styled
                    div
                    [ Typography.center, Typography.display1 ]
                    [ (toString total) ++ results |> text ]
                ]

        pagination =
            viewPagination model

        cells =
            List.concat [ pagination, documents, pagination ]
    in
        if model.loading then
            text ""
        else if searched then
            grid [] (title :: cells)
        else
            grid [] cells



--


view : Model -> Html.Html Msg
view model =
    div []
        [ viewForm model
        , viewDocuments model
        ]
