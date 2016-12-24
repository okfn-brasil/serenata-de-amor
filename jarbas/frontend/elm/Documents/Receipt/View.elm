module Documents.Receipt.View exposing (view)

import Html exposing (a, div, text)
import Html.Attributes exposing (href, target, class)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material.Button as Button
import Material.Icon as Icon
import Material.Options as Options
import Material.Spinner as Spinner
import Documents.Receipt.Model exposing (Model)
import Documents.Receipt.Update exposing (Msg(Mdl, SearchReceipt))


view : Model -> Html.Html Msg
view model =
    case model.url of
        Just url ->
            a
                [ href url, target "_blank", class "receipt view-receipt" ]
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
                    , Button.onClick (SearchReceipt model.reimbursement)
                    , Options.cs "receipt fetch-receipt"
                    ]
                    [ Icon.i "search"
                    , text (translate model.lang ReceiptFetch)
                    ]
