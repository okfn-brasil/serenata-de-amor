module Main exposing (..)

import Html exposing (..)
import Html.Attributes exposing (class, disabled, href, placeholder, type', value)
import Html.Events exposing (onInput, onSubmit)
import Html.App
import Http
import Json.Decode
import Json.Decode.Pipeline exposing (required, decode)
import Task


--
-- Model
--


type alias Document =
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
    , document_number : Int
    , document_type : Int
    , issue_date : String
    , document_value : Float
    , remark_value : Float
    , net_value : Float
    , month : Int
    , year : Int
    , installment : Int
    , passenger : String
    , leg_of_the_trip : Int
    , batch_number : Int
    , reimbursement_number : Int
    , reimbursement_value : Float
    , applicant_id : Int
    }


type alias Model =
    { documentId : String
    , document : Maybe Document
    , loading : Bool
    , error : Maybe Http.Error
    , title : String
    , github :
        { main : String
        , api : String
        }
    }


initialModel : Model
initialModel =
    { documentId = ""
    , document = Nothing
    , loading = False
    , error = Nothing
    , title = "Serenata de Amor"
    , github =
        { main = "http://github.com/datasciencebr/serenata-de-amor"
        , api = "http://github.com/datasciencebr/serenata-de-amor-api"
        }
    }



--
-- Update
--


type Msg
    = Change String
    | Submit
    | ApiFail Http.Error
    | ApiSuccess Document


loadDocument : String -> Cmd Msg
loadDocument documentId =
    Task.perform
        ApiFail
        ApiSuccess
        (Http.get documentDecoder <| "/api/document/" ++ documentId)


documentDecoder : Json.Decode.Decoder Document
documentDecoder =
    decode Document
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
        |> required "document_number" Json.Decode.int
        |> required "document_type" Json.Decode.int
        |> required "issue_date" Json.Decode.string
        |> required "document_value" Json.Decode.float
        |> required "remark_value" Json.Decode.float
        |> required "net_value" Json.Decode.float
        |> required "month" Json.Decode.int
        |> required "year" Json.Decode.int
        |> required "installment" Json.Decode.int
        |> required "passenger" Json.Decode.string
        |> required "leg_of_the_trip" Json.Decode.int
        |> required "batch_number" Json.Decode.int
        |> required "reimbursement_number" Json.Decode.int
        |> required "reimbursement_value" Json.Decode.float
        |> required "applicant_id" Json.Decode.int


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Change documentId ->
            ( { model | documentId = documentId }, Cmd.none )

        Submit ->
            ( { model | loading = True }, loadDocument model.documentId )

        ApiSuccess document ->
            ( { model | document = Just document, loading = False }, Cmd.none )

        ApiFail error ->
            ( { model | document = Nothing, error = Just error, loading = False }, Cmd.none )



--
-- View
--


viewWrapper : Html.Html Msg -> Html.Html Msg
viewWrapper html =
    div [ class "outer" ] [ div [ class "inner" ] [ html ] ]


viewHeader : Model -> Html.Html Msg
viewHeader model =
    div [ class "header" ] [ h1 [] [ text model.title ] ]


viewForm : String -> Bool -> Html.Html Msg
viewForm documentId loading =
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
                , value documentId
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


viewDocument : Maybe Document -> Maybe Http.Error -> Html.Html Msg
viewDocument document error =
    case document of
        Just document ->
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
                    , ( "Document number", toString document.document_number )
                    , ( "Document type", toString document.document_type )
                    , ( "Issue date", document.issue_date )
                    , ( "Document value", toString document.document_value )
                    , ( "Remark value", toString document.remark_value )
                    , ( "Net value", toString document.net_value )
                    , ( "Month", toString document.month )
                    , ( "Year", toString document.year )
                    , ( "Installment", toString document.installment )
                    , ( "Passenger", document.passenger )
                    , ( "Leg of the trip", toString document.leg_of_the_trip )
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
                            , td [] [ a [ href receiptUrl ] [ text receiptUrl ] ] ]
                            ]
            in
                div
                    []
                    [ h2 [] [ text "Document information" ]
                    , table [] rows
                    ]

        Nothing ->
            viewError error


viewDocumentRow : ( String, String ) -> Html.Html Msg
viewDocumentRow ( header, content ) =
    tr
        []
        [ th [] [ text header ]
        , td [] [ text content ]
        ]


viewFooter : Model -> Html.Html Msg
viewFooter model =
    div [ class "footer" ]
        [ ul
            []
            [ li [] [ a [ href model.github.main ] [ text <| "About " ++ model.title ] ]
            , li [] [ a [ href model.github.api ] [ text "Fork me on GitHub" ] ]
            ]
        ]


view : Model -> Html.Html Msg
view model =
    div
        []
        [ viewWrapper <| viewHeader model
        , viewWrapper <| viewForm model.documentId model.loading
        , viewWrapper <| viewDocument model.document model.error
        , viewWrapper <| viewFooter model
        ]



--
-- Init
--


main : Platform.Program Never
main =
    Html.App.program
        { init = ( initialModel, Cmd.none )
        , update = update
        , view = view
        , subscriptions = (\_ -> Sub.none)
        }
