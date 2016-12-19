module Documents.Supplier.View exposing (view)

import Html exposing (a, br, div, img, p, span, text)
import Html.Attributes exposing (href, src, style, target)
import Http exposing (url)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material.Icon as Icon
import Material.Options as Options
import Material.Typography as Typography
import Documents.Supplier.Update exposing (Msg)
import Documents.Supplier.Model exposing (Model, Supplier, Activity)


streetImageUrl : String -> Int -> Int -> String -> String -> Int -> String
streetImageUrl apiKey width height latitude longitude heading =
    url
        "https://maps.googleapis.com/maps/api/streetview"
        [ ( "size", (toString width) ++ "x" ++ (toString height) )
        , ( "location", latitude ++ "," ++ longitude )
        , ( "fov", "90" )
        , ( "heading", toString heading )
        , ( "pitch", "10" )
        , ( "key", apiKey )
        ]


streetImageTag : String -> Maybe String -> Maybe String -> Int -> Html.Html Msg
streetImageTag apiKey latitude longitude heading =
    case latitude of
        Just lat ->
            case longitude of
                Just long ->
                    let
                        source =
                            streetImageUrl apiKey 640 400 lat long heading

                        css =
                            [ ( "width", "50%" )
                            , ( "display", "inline-block" )
                            , ( "margin", "1rem 0 0 0" )
                            ]
                    in
                        a
                            [ href source, target "_blank" ]
                            [ img [ src source, style css ] [] ]

                Nothing ->
                    text ""

        Nothing ->
            text ""


viewImage : String -> Supplier -> Html.Html Msg
viewImage apiKey supplier =
    let
        images =
            List.map
                (streetImageTag apiKey supplier.latitude supplier.longitude)
                [ 90, 180, 270, 360 ]
    in
        div [] images


viewSupplier : Language -> String -> Supplier -> Html.Html Msg
viewSupplier lang apiKey supplier =
    let
        labels =
            [ ( (translate lang SupplierCNPJ), supplier.cnpj )
            , ( (translate lang SupplierTradeName), Maybe.withDefault "" supplier.trade_name )
            , ( (translate lang SupplierName), Maybe.withDefault "" supplier.name )
            , ( (translate lang SupplierOpeningDate), Maybe.withDefault "" supplier.opening )
            , ( (translate lang SupplierLegalEntity), Maybe.withDefault "" supplier.legal_entity )
            , ( (translate lang SupplierType), Maybe.withDefault "" supplier.supplier_type )
            , ( (translate lang SupplierStatus), Maybe.withDefault "" supplier.status )
            , ( (translate lang SupplierSituation), Maybe.withDefault "" supplier.situation )
            , ( (translate lang SupplierSituationReason), Maybe.withDefault "" supplier.situation_reason )
            , ( (translate lang SupplierSituationDate), Maybe.withDefault "" supplier.situation_date )
            , ( (translate lang SupplierSpecialSituation), Maybe.withDefault "" supplier.special_situation )
            , ( (translate lang SupplierSpecialSituationDate), Maybe.withDefault "" supplier.special_situation_date )
            , ( (translate lang SupplierResponsibleFederativeEntity), Maybe.withDefault "" supplier.responsible_federative_entity )
            , ( (translate lang SupplierAddress), Maybe.withDefault "" supplier.address )
            , ( (translate lang SupplierNumber), Maybe.withDefault "" supplier.address_number )
            , ( (translate lang SupplierAdditionalAddressDetails), Maybe.withDefault "" supplier.additional_address_details )
            , ( (translate lang SupplierNeighborhood), Maybe.withDefault "" supplier.neighborhood )
            , ( (translate lang SupplierZipCode), Maybe.withDefault "" supplier.zip_code )
            , ( (translate lang SupplierCity), Maybe.withDefault "" supplier.city )
            , ( (translate lang SupplierState), Maybe.withDefault "" supplier.state )
            , ( (translate lang SupplierEmail), Maybe.withDefault "" supplier.email )
            , ( (translate lang SupplierPhone), Maybe.withDefault "" supplier.phone )
            , ( (translate lang SupplierLastUpdated), Maybe.withDefault "" supplier.last_updated )
            ]

        rows =
            List.map viewRow labels

        activities =
            List.map
                viewActivities
                [ ( (translate lang SupplierMainActivity), supplier.main_activity )
                , ( (translate lang SupplierSecondaryActivity), supplier.secondary_activity )
                ]

        icon =
            Icon.view "store" [ Options.css "transform" "translateY(0.4rem)" ]

        title =
            " " ++ (Maybe.withDefault "" supplier.name)

        source =
            "http://www.receita.fazenda.gov.br/PessoaJuridica/CNPJ/cnpjreva/cnpjreva_solicitacao2.asp"
    in
        div
            []
            [ Options.styled
                p
                [ Typography.subhead ]
                [ icon, text title, viewImage apiKey supplier ]
            , Options.styled div [] (rows ++ activities)
            , Options.styled
                p
                [ Typography.caption, Options.css "margin-top" "1rem" ]
                [ text (translate lang SupplierSource)
                , a [ href source ] [ text (translate lang SupplierFederalRevenue) ]
                ]
            ]


viewRow : ( String, String ) -> Html.Html Msg
viewRow ( label, value ) =
    let
        styles =
            [ Options.css "display" "flex"
            , Options.css "justify-content" "space-between"
            , Options.css "align-items" "center"
            ]

        labelStyles =
            Options.css "width" "30%" :: styles
    in
        Options.styled div
            [ Options.css "display" "flex"
            , Options.css "flex-direction" "row"
            ]
            [ Options.styled span (Typography.body2 :: labelStyles) [ text label ]
            , Options.styled span (Typography.body1 :: styles) [ text value ]
            ]


viewActivity : Activity -> Html.Html Msg
viewActivity activity =
    activity.code ++ " " ++ activity.description |> text


viewActivities : ( String, List Activity ) -> Html.Html Msg
viewActivities ( label, activities ) =
    let
        value =
            List.map viewActivity activities
                |> List.intersperse (br [] [])
    in
        Options.styled div
            []
            [ Options.styled span [ Typography.body2 ] [ text label ]
            , br [] []
            , Options.styled span [ Typography.body1 ] value
            ]


view : Model -> Html.Html Msg
view model =
    if model.loaded then
        case model.supplier of
            Just info ->
                viewSupplier model.lang model.googleStreetViewApiKey info

            Nothing ->
                Options.styled div
                    [ Typography.caption ]
                    [ text "CNPJ invalid or not found." ]
    else if model.loading then
        Options.styled div
            [ Typography.caption ]
            [ text "Fetching supplier info from CNPJ…" ]
    else
        text ""
