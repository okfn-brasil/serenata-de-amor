module Documents.Receipt.View exposing (view)

import Html exposing (a, button, div, text)
import Html.Attributes exposing (href)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material.Button as Button
import Material.Icon as Icon
import Material.Spinner as Spinner
import Documents.Receipt.Model exposing (Model)
import Documents.Receipt.Update exposing (Msg(Mdl, LoadUrl))


view : Int -> Model -> Html.Html Msg
view id model =
    case model.url of
        Just url ->
            a
                [ href url ]
                [ Button.render
                    Mdl
                    [ 1 ]
                    model.mdl
                    [ Button.minifab ]
                    [ Icon.i "receipt"
                    , text (translate model.lang ReceiptAvailable)
                    ]
                ]

        Nothing ->
            if model.fetched then
                Button.render Mdl
                    [ 2 ]
                    model.mdl
                    [ Button.minifab
                    , Button.disabled
                    ]
                    [ Icon.i "receipt"
                    , text (translate model.lang ReceiptNotAvailable)
                    ]
            else if model.loading then
                Spinner.spinner [ Spinner.active True ]
            else
                Button.render Mdl
                    [ 0 ]
                    model.mdl
                    [ Button.minifab
                    , Button.onClick (LoadUrl id)
                    ]
                    [ Icon.i "search"
                    , text (translate model.lang ReceiptFetch)
                    ]
