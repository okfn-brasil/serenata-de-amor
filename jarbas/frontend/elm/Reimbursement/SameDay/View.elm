module Reimbursement.SameDay.View exposing (view)

import Html
import Internationalization exposing (TranslationId(..), translate)
import Reimbursement.RelatedTable.Model exposing (Model)
import Reimbursement.RelatedTable.Update exposing (Msg)
import Reimbursement.RelatedTable.View as RelatedTable


view : Model -> Html.Html Msg
view model =
    SameDayTitle
        |> translate model.lang
        |> RelatedTable.view model
