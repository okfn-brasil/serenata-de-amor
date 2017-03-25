module Reimbursement.RelatedTable.View exposing (view)

import Array
import Format.Price exposing (formatPrice)
import Html exposing (a, br, div, p, text)
import Html.Attributes exposing (attribute, class, href, style, target)
import Html.Events exposing (onClick, onMouseEnter, onMouseLeave)
import Internationalization.Types exposing (Language)
import Material
import Material.Icon as Icon
import Material.Options as Options
import Material.Typography as Typography
import Reimbursement.RelatedTable.Model exposing (Model, ReimbursementSummary)
import Reimbursement.RelatedTable.Update exposing (Msg(..), getReimbursementUrl)


viewReimbursement : Language -> Material.Model -> ( Int, ReimbursementSummary ) -> Html.Html Msg
viewReimbursement lang mdl ( index, reimbursement ) =
    let
        city =
            reimbursement.city
                |> Maybe.withDefault ""
                |> (++) " "
                |> text

        baseStyles =
            [ ( "align-items", "center" )
            , ( "color", "rgba(0, 0, 0, 0.870588)" )
            , ( "justify-content", "space-between" )
            , ( "margin-bottom", "1em" )
            , ( "display", "flex" )
            , ( "padding-right", "1rem" )
            , ( "text-decoration", "none" )
            ]

        styles =
            let
                merged =
                    if reimbursement.over then
                        List.append
                            baseStyles
                            [ ( "cursor", "pointer" )
                            , ( "background-color", "#efefef" )
                            ]
                    else
                        baseStyles
            in
                List.map (\( prop, val ) -> Options.css prop val) merged

        attributesAndEvents =
            List.map
                (\e -> Options.attribute e)
                [ MouseOver index True |> onMouseEnter
                , MouseOver index False |> onMouseLeave
                , getReimbursementUrl reimbursement |> href
                , target "_blank"
                , reimbursement.subquotaId |> toString |> attribute "data-baseSyles"
                , reimbursement.year |> toString |> attribute "data-year"
                , reimbursement.applicantId |> toString |> attribute "data-applicant"
                , reimbursement.documentId |> toString |> attribute "data-document"
                ]

        attr =
            [ Options.cs "same-day" ]
                |> List.append attributesAndEvents
                |> List.append styles
    in
        Options.styled
            a
            attr
            [ Options.span
                []
                [ Options.span [] [ text reimbursement.supplier ]
                , Options.span [ Typography.caption ] [ city ]
                , br [] []
                , Options.span [ Typography.caption ] [ text reimbursement.subquotaDescription ]
                ]
            , Options.span
                [ Options.css "white-space" "nowrap" ]
                [ reimbursement.totalNetValue |> formatPrice lang |> text ]
            ]


view : Model -> String -> Html.Html Msg
view model title =
    if Array.isEmpty model.results.reimbursements then
        text ""
    else
        div []
            [ Options.styled
                p
                [ Typography.subhead
                , Options.css "margin-top" "2em"
                ]
                [ Icon.view
                    "today"
                    [ Options.css "transform" "translateY(0.4rem)" ]
                , text title
                ]
            , model.results.reimbursements
                |> Array.toIndexedList
                |> List.map (viewReimbursement model.lang model.mdl)
                |> Options.styled div []
            ]
