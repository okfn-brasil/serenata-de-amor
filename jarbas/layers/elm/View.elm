module View exposing (view)

import Html
import Layout
import Material.Layout
import Model exposing (Model)
import Reimbursement.View
import Update exposing (Msg(..))


view : Model -> Html.Html Msg
view model =
    let
        header =
            Html.map LayoutMsg <| Layout.header model.layout

        drawer =
            List.map (\x -> Html.map LayoutMsg x) (Layout.drawer model.layout)

        reimbursements =
            Html.map ReimbursementMsg <| Reimbursement.View.view model.reimbursements
    in
        Material.Layout.render
            Mdl
            model.mdl
            [ Material.Layout.fixedHeader ]
            { header = [ header ]
            , drawer = drawer
            , tabs = ( [], [] )
            , main = [ reimbursements ]
            }
