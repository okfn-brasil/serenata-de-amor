module Document exposing (Msg, Model, loadDocuments, update, view)

import Html exposing (a, button, div, form, input, h2, table, td, text, th, tr)
import Html.Attributes exposing (class, disabled, href, placeholder, type', value)
import Html.Events exposing (onInput, onSubmit)
import Http
import Json.Decode
import Json.Decode exposing ((:=))
import Json.Decode.Pipeline exposing (required, decode)
import String
import Task


--
-- Model
--


type alias SingleModel =
    { document_id : Int
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
    , issue_date : String
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
    }


type alias Model =
    { results : List SingleModel
    , query : String
    , loading : Bool
    , error : Maybe Http.Error
    }



--
-- Update
--


type Msg
    = Change String
    | Submit
    | ApiFail Http.Error
    | ApiSuccess (List SingleModel)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Change query ->
            ( { model | query = (String.trim query) }, Cmd.none )

        Submit ->
            ( { model | loading = True }, loadDocuments model.query )

        ApiSuccess results ->
            ( { model | results = results, loading = False }, Cmd.none )

        ApiFail error ->
            ( { model | error = Just error, loading = False }, Cmd.none )


loadDocuments : String -> Cmd Msg
loadDocuments query =
    let
        url =
            Http.url "/api/document/" [ ( "document_id", query ) ]
    in
        Task.perform
            ApiFail
            ApiSuccess
            (Http.get decoder url)



--
-- Decoders
--


decoder : Json.Decode.Decoder (List SingleModel)
decoder =
    Json.Decode.at [ "results" ] <| Json.Decode.list singleDecoder


singleDecoder : Json.Decode.Decoder SingleModel
singleDecoder =
    decode SingleModel
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
        |> required "issue_date" Json.Decode.string
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



--
-- View
--


viewForm : String -> Bool -> Html.Html Msg
viewForm query loading =
    let
        buttonLabel =
            if loading then
                "Loading"
            else
                "Search"
    in
        form
            [ onSubmit Submit ]
            [ input
                [ type' "text"
                , value query
                , onInput Change
                , disabled loading
                , placeholder "Enter a CEAP document #"
                ]
                []
            , button [ type' "submit", disabled loading ] [ text buttonLabel ]
            ]


viewError : Maybe Http.Error -> Html.Html Msg
viewError error =
    case error of
        Just _ ->
            h2 [ class "error" ] [ text "Document not found" ]

        Nothing ->
            text ""


viewDocument : SingleModel -> Html.Html Msg
viewDocument document =
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
            , ( "Issue date", document.issue_date )
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

        receiptUrl =
            "http://www.camara.gov.br/cota-parlamentar/documentos/publ/"
                ++ toString document.applicant_id
                ++ "/"
                ++ toString document.year
                ++ "/"
                ++ toString document.document_id
                ++ ".pdf"

        rows =
            List.append
                (List.map viewDocumentRow labels)
                [ tr
                    []
                    [ th [] [ text "Receipt URL" ]
                    , td [] [ a [ href receiptUrl ] [ text receiptUrl ] ]
                    ]
                ]

        title =
            "Document #" ++ (toString document.document_id)
    in
        div
            []
            [ h2 [] [ text title ]
            , table [] rows
            ]


viewDocuments : List SingleModel -> Html.Html Msg
viewDocuments documents =
    if List.length documents == 0 then
        viewError Nothing
    else
        div [] (List.map viewDocument documents)


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
        [ viewForm model.query model.loading
        , viewDocuments model.results
        ]
