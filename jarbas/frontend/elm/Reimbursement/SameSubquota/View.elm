module Reimbursement.SameSubquota.View exposing (view)

import Reimbursement.RelatedTable.Model exposing (Model)
import Reimbursement.RelatedTable.View as RelatedTable
import Reimbursement.RelatedTable.Update exposing (Msg)
import Html
import Internationalization exposing (TranslationId(..), translate)


view : Model -> Html.Html Msg
view model =
    SameSubquotaTitle
        |> translate model.lang
        |> RelatedTable.view model
