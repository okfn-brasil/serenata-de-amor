module View exposing (view)

import Documents.View
import Html
import Layout
import Material.Layout
import Model exposing (Model)
import Update exposing (Msg(..))


view : Model -> Html.Html Msg
view model =
    let
        header =
            Html.map LayoutMsg <| Layout.header model.layout

        drawer =
            List.map (\x -> Html.map LayoutMsg x) (Layout.drawer model.layout)

        documents =
            Html.map DocumentsMsg <| Documents.View.view model.documents
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
