module Document exposing (Msg, Model, initialModel, loadDocuments, updateFormFields, update, view)

import Dict exposing (Dict)
import Html exposing (a, button, div, form, input, h2, h3, hr, label, table, td, text, th, tr)
import Html.App
import Html.Attributes exposing (class, disabled, for, href, id, type', value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode
import Json.Decode.Pipeline exposing (decode, hardcoded, required)
import Navigation
import Receipt
import String
import Supplier
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


type alias FormField =
    { label : String
    , selected : Bool
    , value : String
    }


type alias Form =
    Dict String FormField


type alias Model =
    { results : Results
    , form : Form
    , loading : Bool
    , error : Maybe Http.Error
    }


fieldsAndLabels : List ( String, String )
fieldsAndLabels =
    [ ( "document_id", "Document ID" )
    , ( "congressperson_name", "Congressperson name" )
    , ( "congressperson_id", "Congressperson ID" )
    , ( "congressperson_document", "Congressperson document" )
    , ( "term", "Term" )
    , ( "state", "State" )
    , ( "party", "Party" )
    , ( "term_id", "Term ID" )
    , ( "subquota_number", "Subquota number" )
    , ( "subquota_description", "Subquota description" )
    , ( "subquota_group_id", "Subquota group ID" )
    , ( "subquota_group_description", "Subquota group description" )
    , ( "supplier", "Supplier" )
    , ( "cnpj_cpf", "CNPJ or CPF" )
    , ( "document_number", "Document number" )
    , ( "document_type", "Document type" )
    , ( "issue_date", "Issue date" )
    , ( "document_value", "Document value" )
    , ( "remark_value", "Remark value" )
    , ( "net_value", "Net value" )
    , ( "month", "Month" )
    , ( "year", "Year" )
    , ( "installment", "Installment" )
    , ( "passenger", "Passenger" )
    , ( "leg_of_the_trip", "Leg of the trip" )
    , ( "batch_number", "Batch number" )
    , ( "reimbursement_number", "Reimbursement number" )
    , ( "reimbursement_value", "Reimbursement value" )
    , ( "applicant_id", "Applicant ID" )
    ]


isSearchable : ( String, String ) -> Bool
isSearchable fieldAndLabel =
    let
        field =
            fst fieldAndLabel

        searchable =
            [ "applicant_id"
            , "cnpj_cpf"
            , "congressperson_id"
            , "document_id"
            , "document_type"
            , "month"
            , "party"
            , "reimbursement_number"
            , "state"
            , "subquota_group_id"
            , "subquota_number"
            , "term"
            , "year"
            ]
    in
        List.member field searchable


toFormField : ( String, String ) -> ( String, FormField )
toFormField ( name, label ) =
    ( name
    , FormField label False ""
    )


initialResults : Results
initialResults =
    Results [] Nothing


initialForm : Form
initialForm =
    List.filter isSearchable fieldsAndLabels
        |> List.map toFormField
        |> Dict.fromList


initialModel : Model
initialModel =
    Model initialResults initialForm False Nothing


getQuery : Form -> List ( String, String )
getQuery form =
    form
        |> Dict.filter (\index field -> not (String.isEmpty field.value))
        |> Dict.map (\index field -> field.value)
        |> Dict.toList



--
-- Update
--


type Msg
    = Change String String
    | Submit
    | ApiFail Http.Error
    | ApiSuccess Results
    | ReceiptMsg Int Receipt.Msg
    | SupplierMsg Int Supplier.Msg


updateFormField : Form -> String -> String -> Form
updateFormField form name value =
    let
        formField =
            Dict.get name form
    in
        case formField of
            Just field ->
                Dict.insert name { field | value = value } form

            Nothing ->
                form


updateFormFields : Form -> List ( String, String ) -> Form
updateFormFields form queryList =
    let
        maybeQuery =
            List.head queryList

        remainingQueries =
            List.drop 1 queryList
    in
        case maybeQuery of
            Just query ->
                let
                    newForm =
                        updateFormField form (fst query) (snd query)
                in
                    updateFormFields newForm remainingQueries

            Nothing ->
                form


updateSupplier : Int -> Supplier.Msg -> ( Int, SingleModel ) -> ( SingleModel, Cmd Msg )
updateSupplier target msg ( index, document ) =
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


updateReceipt : Int -> Receipt.Msg -> ( Int, SingleModel ) -> ( SingleModel, Cmd Msg )
updateReceipt target msg ( index, document ) =
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


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Change name value ->
            let
                form =
                    updateFormField model.form name value
            in
                ( { model | form = form }, Cmd.none )

        Submit ->
            let
                url =
                    getQuery model.form |> toUrl
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

        ReceiptMsg index receiptMsg ->
            getDocumentsAndCmd model index updateReceipt receiptMsg

        SupplierMsg index supplierMsg ->
            getDocumentsAndCmd model index updateSupplier supplierMsg


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
            List.filter isSearchable query

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


decoder : Json.Decode.Decoder Results
decoder =
    Json.Decode.object2 Results
        (Json.Decode.at [ "results" ] <| Json.Decode.list singleDecoder)
        (Json.Decode.at [ "count" ] <| Json.Decode.Pipeline.nullable Json.Decode.int)


receiptDecoder : Json.Decode.Decoder Receipt.Model
receiptDecoder =
    decode Receipt.Model
        |> required "url" (Json.Decode.Pipeline.nullable Json.Decode.string)
        |> required "fetched" Json.Decode.bool
        |> hardcoded False
        |> hardcoded Nothing


singleDecoder : Json.Decode.Decoder SingleModel
singleDecoder =
    decode SingleModel
        |> required "id" Json.Decode.int
        |> required "document_id" Json.Decode.int
        |> required "congressperson_name" Json.Decode.string
        |> required "congressperson_id" Json.Decode.int
        |> required "congressperson_document" Json.Decode.int
        |> required "term" Json.Decode.int
        |> required "state" Json.Decode.string
        |> required "party" Json.Decode.string
        |> required "term_id" Json.Decode.int
        |> required "subquota_number" Json.Decode.int
        |> required "subquota_description" Json.Decode.string
        |> required "subquota_group_id" Json.Decode.int
        |> required "subquota_group_description" Json.Decode.string
        |> required "supplier" Json.Decode.string
        |> required "cnpj_cpf" Json.Decode.string
        |> required "document_number" Json.Decode.string
        |> required "document_type" Json.Decode.int
        |> required "issue_date" (Json.Decode.Pipeline.nullable Json.Decode.string)
        |> required "document_value" Json.Decode.string
        |> required "remark_value" Json.Decode.string
        |> required "net_value" Json.Decode.string
        |> required "month" Json.Decode.int
        |> required "year" Json.Decode.int
        |> required "installment" Json.Decode.int
        |> required "passenger" Json.Decode.string
        |> required "leg_of_the_trip" Json.Decode.string
        |> required "batch_number" Json.Decode.int
        |> required "reimbursement_number" Json.Decode.int
        |> required "reimbursement_value" Json.Decode.string
        |> required "applicant_id" Json.Decode.int
        |> required "receipt" receiptDecoder
        |> hardcoded Supplier.initialModel



--
-- View
--


viewFormField : Bool -> ( String, FormField ) -> Html.Html Msg
viewFormField loading ( fieldName, field ) =
    div
        [ class "field" ]
        [ label [ for <| "id_" ++ fieldName ] [ text field.label ]
        , input
            [ type' "text"
            , id <| "id_" ++ fieldName
            , value field.value
            , Change fieldName |> onInput
            , disabled loading
            ]
            []
        ]


viewForm : Model -> Html.Html Msg
viewForm model =
    let
        buttonLabel =
            if model.loading then
                "Loading…"
            else
                "Search"

        fields =
            Dict.toList model.form

        inputs =
            List.map (viewFormField model.loading) fields

        sendButton =
            [ button [ type' "submit", disabled model.loading ] [ text buttonLabel ] ]

        children =
            [ div [ class "fields" ] inputs
            , div [ class "fields" ] sendButton
            ]
    in
        form [ onSubmit Submit ] children


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
            Html.App.map (ReceiptMsg index) (Receipt.view index document.receipt)

        rows =
            List.append
                (List.map viewDocumentRow labels)
                [ tr
                    []
                    [ th [] [ text "Receipt URL" ]
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
