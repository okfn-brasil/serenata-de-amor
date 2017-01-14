module Reimbursement.RelatedTable.Update exposing (Msg(..), getReimbursementUrl, loadUrl, update, updateParentId)

import Reimbursement.RelatedTable.Decoder exposing (decoder)
import Reimbursement.RelatedTable.Model exposing (Model, ReimbursementSummary, Results)
import Http
import Material
import String


type Msg
    = LoadRelatedTable (Result Http.Error Results)
    | MouseOver Int Bool
    | Mdl (Material.Msg Msg)


updateParentId : Int -> Model -> Model
updateParentId parentId model =
    { model | parentId = Just parentId }


updateReimbursements : Int -> Bool -> ( Int, ReimbursementSummary ) -> ReimbursementSummary
updateReimbursements target mouseOver ( index, reimbursement ) =
    if target == index then
        { reimbursement | over = mouseOver }
    else
        reimbursement


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
                newReimbursements =
                    results.reimbursements
                        |> List.filter (isParent model >> not)
                        |> List.append model.results.reimbursements

                nextPageUrl =
                    results.nextPageUrl

                newResults =
                    { reimbursements = newReimbursements, nextPageUrl = nextPageUrl }

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
                newReimbursements =
                    model.results.reimbursements
                        |> List.indexedMap (,)
                        |> List.map (updateReimbursements target mouseOver)

                results =
                    model.results

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
