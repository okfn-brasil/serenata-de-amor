module Documents.RelatedTable.View exposing (view)

import Documents.RelatedTable.Model exposing (DocumentSummary, Model)
import Documents.RelatedTable.Update exposing (Msg(..), getDocumentUrl)
import Format.Price exposing (formatPrice)
import Html exposing (a, br, div, p, text)
import Html.Attributes exposing (attribute, class, href, style, target)
import Html.Events exposing (onClick, onMouseEnter, onMouseLeave)
import Material
import Material.Icon as Icon
import Material.Options as Options
import Material.Typography as Typography
import Internationalization exposing (Language)


viewDocument : Language -> Material.Model -> ( Int, DocumentSummary ) -> Html.Html Msg
viewDocument lang mdl ( index, document ) =
    let
        city =
            document.city
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
                    if document.over then
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
                , getDocumentUrl document |> href
                , target "_blank"
                , document.subquotaId |> toString |> attribute "data-baseSyles"
                , document.year |> toString |> attribute "data-year"
                , document.applicantId |> toString |> attribute "data-applicant"
                , document.documentId |> toString |> attribute "data-document"
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
                [ Options.span [] [ text document.supplier ]
                , Options.span [ Typography.caption ] [ city ]
                , br [] []
                , Options.span [ Typography.caption ] [ text document.subquotaDescription ]
                ]
            , Options.span
                [ Options.css "white-space" "nowrap" ]
                [ document.totalNetValue |> formatPrice lang |> text ]
            ]


view : Model -> String -> Html.Html Msg
view model title =
    if List.isEmpty model.results.documents then
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
            , model.results.documents
                |> List.indexedMap (,)
                |> List.map (viewDocument model.lang model.mdl)
                |> Options.styled div []
            ]
