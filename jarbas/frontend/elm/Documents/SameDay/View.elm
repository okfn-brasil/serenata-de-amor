module Documents.SameDay.View exposing (view)

import Documents.SameDay.Model exposing (DocumentSummary, Model)
import Documents.SameDay.Update exposing (Msg(..))
import Format.Price exposing (formatPrice)
import Html exposing (a, br, div, p, text)
import Html.Attributes exposing (attribute, class, href, style)
import Html.Events exposing (onClick, onMouseEnter, onMouseLeave)
import Material
import Material.Icon as Icon
import Material.Options as Options
import Material.Typography as Typography
import Internationalization exposing (Language, TranslationId(..), translate)


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
            , ( "justify-content", "space-between" )
            , ( "margin-bottom", "1em" )
            , ( "display", "flex" )
            , ( "padding-right", "1rem" )
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
                , GoTo document |> onClick
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
            div
            attr
            [ Options.span
                []
                [ Options.span [] [ text document.supplier ]
                , Options.span [ Typography.caption ] [ city ]
                , br [] []
                , Options.span [ Typography.caption ] [ text document.subquotaDescription ]
                ]
            , Options.span [] [ document.totalNetValue |> formatPrice lang |> text ]
            ]


view : Model -> Html.Html Msg
view model =
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
                , translate model.lang SameDayTitle |> text
                ]
            , model.results.documents
                |> List.indexedMap (,)
                |> List.map (viewDocument model.lang model.mdl)
                |> Options.styled div []
            ]
