module View exposing (view)

import Documents.View
import Html
import Html.App
import Layout
import Material.Layout
import Model exposing (Model)
import Update exposing (Msg(..))


view : Model -> Html.Html Msg
view model =
    let
        header =
            Html.App.map LayoutMsg <| Layout.header model.layout

        drawer =
            List.map (\x -> Html.App.map LayoutMsg x) (Layout.drawer model.layout)

        documents =
            Html.App.map DocumentsMsg <| Documents.View.view model.documents
    in
        Material.Layout.render
            Mdl
            model.mdl
            [ Material.Layout.fixedHeader ]
            { header = [ header ]
            , drawer = drawer
            , tabs = ( [], [] )
            , main = [ documents ]
            }
