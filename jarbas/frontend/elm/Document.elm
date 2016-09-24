module Document exposing (Msg, Model, initialModel, loadDocuments, updateFormFields, update, view)

import Dict exposing (Dict)
import Html exposing (a, button, div, form, input, h2, h3, label, table, td, text, th, tr)
import Html.Attributes exposing (class, disabled, for, href, id, type', value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode exposing ((:=))
import Json.Decode.Pipeline exposing (decode, hardcoded, required)
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
    , receipt_url : Maybe String
    , receipt_fetched : Bool
    , receipt_loading : Bool
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
    | FetchReceipt Int Int
    | ReceiptSuccess Int (Maybe String)
    | ReceiptFail Http.Error


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


updateReceipt : Int -> Maybe String -> ( Int, SingleModel ) -> SingleModel
updateReceipt target url ( index, document ) =
    if target == index then
        { document
            | receipt_url = url
            , receipt_fetched = True
            , receipt_loading = False
        }
    else
        document


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

        ApiSuccess results ->
            ( { model | results = results, loading = False, error = Nothing }, Cmd.none )

        ApiFail error ->
            ( { model | results = initialResults, error = Just error, loading = False }, Cmd.none )

        FetchReceipt index id ->
            ( model, fetchReceipt index id )

        ReceiptSuccess index url ->
            let
                results =
                    model.results

                documents =
                    results.documents

                indexedDocuments =
                    List.indexedMap (,) documents

                newDocuments =
                    List.map (updateReceipt index url) indexedDocuments

                newResults =
                    { results | documents = newDocuments }
            in
                ( { model | results = newResults }, Cmd.none )

        ReceiptFail error ->
            let
                results =
                    model.results

                documents =
                    results.documents

                newDocuments =
                    List.map (\d -> { d | receipt_loading = False }) documents

                newResults =
                    { results | documents = newDocuments }
            in
                ( { model | results = results, error = Just error }, Cmd.none )


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


fetchReceipt : Int -> Int -> Cmd Msg
fetchReceipt index id =
    let
        url =
            "/api/receipt/" ++ (toString id) ++ "/"
    in
        Task.perform
            ReceiptFail
            (ReceiptSuccess index)
            (Http.get receiptDecoder url)


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
        |> required "receipt_url" (Json.Decode.Pipeline.nullable Json.Decode.string)
        |> required "receipt_fetched" Json.Decode.bool
        |> hardcoded False


receiptDecoder : Json.Decode.Decoder (Maybe String)
receiptDecoder =
    Json.Decode.at [ "url" ] (Json.Decode.maybe Json.Decode.string)



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


viewReceipt : Int -> SingleModel -> Html.Html Msg
viewReceipt index document =
    case document.receipt_url of
        Just url ->
            a [ href url ] [ text url ]

        Nothing ->
            if document.receipt_fetched then
                div [] [ text "Not available" ]
            else
                let
                    label =
                        if document.receipt_loading then
                            "Loading…"
                        else
                            "Fetch receipt URL"
                in
                    button
                        [ onClick (FetchReceipt index document.id)
                        , disabled document.receipt_loading
                        ]
                        [ text label ]


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

        rows =
            List.append
                (List.map viewDocumentRow labels)
                [ tr
                    []
                    [ th [] [ text "Receipt URL" ]
                    , td [] [ viewReceipt index document ]
                    ]
                ]

        title =
            "Document #" ++ (toString document.document_id)
    in
        div
            []
            [ h3 [] [ text title ]
            , table [] rows
            ]


viewDocuments : Results -> Html.Html Msg
viewDocuments results =
    if List.length results.documents == 0 then
        viewError Nothing
    else
        let
            documents =
                List.indexedMap (\idx doc -> (viewDocument idx doc)) results.documents

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
