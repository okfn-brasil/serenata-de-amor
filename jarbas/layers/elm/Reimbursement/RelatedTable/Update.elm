module Reimbursement.RelatedTable.Update exposing (Msg(..), getReimbursementUrl, loadUrl, update, updateParentId)

import Array exposing (Array)
import Http
import Material
import Reimbursement.RelatedTable.Decoder exposing (decoder)
import Reimbursement.RelatedTable.Model exposing (Model, ReimbursementSummary, Results)
import String


type Msg
    = LoadRelatedTable (Result Http.Error Results)
    | MouseOver Int Bool
    | Mdl (Material.Msg Msg)


updateParentId : Int -> Model -> Model
updateParentId parentId model =
    { model | parentId = Just parentId }


updateReimbursements : Int -> Bool -> Array ReimbursementSummary -> Array ReimbursementSummary
updateReimbursements target mouseOver reimbursements =
    case Array.get target reimbursements of
        Just reimbursement ->
            Array.set target { reimbursement | over = mouseOver } reimbursements

        Nothing ->
            reimbursements


isParent : Model -> ReimbursementSummary -> Bool
isParent model result =
    case model.parentId of
        Just parentId ->
            result.documentId == parentId

        Nothing ->
            False


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadRelatedTable (Ok results) ->
            let
                newReimbursements : Array ReimbursementSummary
                newReimbursements =
                    results.reimbursements
                        |> Array.filter (isParent model >> not)
                        |> Array.append model.results.reimbursements

                nextPageUrl : Maybe String
                nextPageUrl =
                    results.nextPageUrl

                newResults : Results
                newResults =
                    { reimbursements = newReimbursements, nextPageUrl = nextPageUrl }

                cmd : Cmd Msg
                cmd =
                    case nextPageUrl of
                        Just url ->
                            loadUrl url

                        Nothing ->
                            Cmd.none
            in
                ( { model | results = newResults }, cmd )

        LoadRelatedTable (Err error) ->
            let
                err =
                    Debug.log "ApiFail" (toString error)
            in
                ( model, Cmd.none )

        MouseOver target mouseOver ->
            let
                newReimbursements : Array ReimbursementSummary
                newReimbursements =
                    updateReimbursements target mouseOver model.results.reimbursements

                results : Results
                results =
                    model.results

                newResults : Results
                newResults =
                    { results | reimbursements = newReimbursements }
            in
                ( { model | results = newResults }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


getReimbursementUrl : ReimbursementSummary -> String
getReimbursementUrl reimbursement =
    String.join
        "/"
        [ "#"
        , "year"
        , reimbursement.year |> toString
        , "applicantId"
        , reimbursement.applicantId |> toString
        , "documentId"
        , reimbursement.documentId |> toString
        ]


loadUrl : String -> Cmd Msg
loadUrl url =
    Http.send
        LoadRelatedTable
        (Http.get url decoder)
