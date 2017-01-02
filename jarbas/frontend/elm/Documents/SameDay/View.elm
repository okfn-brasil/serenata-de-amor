module Documents.SameDay.View exposing (view)

import Documents.RelatedTable.Model exposing (Model)
import Documents.RelatedTable.View as RelatedTable
import Documents.RelatedTable.Update exposing (Msg)
import Html
import Internationalization exposing (TranslationId(..), translate)


view : Model -> Html.Html Msg
view model =
    SameDayTitle
        |> translate model.lang
        |> RelatedTable.view model
