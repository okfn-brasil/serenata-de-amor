module Reimbursement.Company.View exposing (view)

import Date
import Format.Date exposing (formatDate)
import Html exposing (a, br, div, img, p, span, text)
import Html.Attributes exposing (class, href, src, style, target)
import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..))
import Material.Icon as Icon
import Material.Options as Options
import Material.Typography as Typography
import Reimbursement.Company.Model exposing (Activity, Company, Model)
import Reimbursement.Company.Update exposing (Msg)


viewDate : Language -> Maybe Date.Date -> String
viewDate lang maybeDate =
    case maybeDate of
        Just date ->
            formatDate lang date

        Nothing ->
            ""


viewCompany : Language -> Maybe String -> Company -> Html.Html Msg
viewCompany lang apiKey company =
    let
        labels =
            [ ( (translate lang CompanyCNPJ), company.cnpj )
            , ( (translate lang CompanyTradeName), Maybe.withDefault "" company.trade_name )
            , ( (translate lang CompanyName), Maybe.withDefault "" company.name )
            , ( (translate lang CompanyOpeningDate), viewDate lang company.opening )
            , ( (translate lang CompanyLegalEntity), Maybe.withDefault "" company.legal_entity )
            , ( (translate lang CompanyType), Maybe.withDefault "" company.company_type )
            , ( (translate lang CompanyStatus), Maybe.withDefault "" company.status )
            , ( (translate lang CompanySituation), Maybe.withDefault "" company.situation )
            , ( (translate lang CompanySituationReason), Maybe.withDefault "" company.situation_reason )
            , ( (translate lang CompanySituationDate), viewDate lang company.situation_date )
            , ( (translate lang CompanySpecialSituation), Maybe.withDefault "" company.special_situation )
            , ( (translate lang CompanySpecialSituationDate), viewDate lang company.special_situation_date )
            , ( (translate lang CompanyResponsibleFederativeEntity), Maybe.withDefault "" company.responsible_federative_entity )
            , ( (translate lang CompanyAddress), Maybe.withDefault "" company.address )
            , ( (translate lang CompanyNumber), Maybe.withDefault "" company.address_number )
            , ( (translate lang CompanyAdditionalAddressDetails), Maybe.withDefault "" company.additional_address_details )
            , ( (translate lang CompanyNeighborhood), Maybe.withDefault "" company.neighborhood )
            , ( (translate lang CompanyZipCode), Maybe.withDefault "" company.zip_code )
            , ( (translate lang CompanyCity), Maybe.withDefault "" company.city )
            , ( (translate lang CompanyState), Maybe.withDefault "" company.state )
            , ( (translate lang CompanyEmail), Maybe.withDefault "" company.email )
            , ( (translate lang CompanyPhone), Maybe.withDefault "" company.phone )
            , ( (translate lang CompanyLastUpdated), viewDate lang company.last_updated )
            ]

        rows =
            List.map viewRow labels

        activities =
            List.map
                viewActivities
                [ ( (translate lang CompanyMainActivity), company.main_activity )
                , ( (translate lang CompanySecondaryActivity), company.secondary_activity )
                ]

        icon =
            Icon.view "store" [ Options.css "transform" "translateY(0.4rem)" ]

        title =
            " " ++ (Maybe.withDefault "" company.name) ++ " "

        location =
            Options.styled
                span
                [ Typography.caption ]
                [ [ company.city, company.state ]
                    |> List.map (Maybe.withDefault "")
                    |> List.filter (String.isEmpty >> not)
                    |> String.join "/"
                    |> text
                ]

        source =
            "http://www.receita.fazenda.gov.br/PessoaJuridica/CNPJ/cnpjreva/cnpjreva_solicitacao2.asp"
    in
        div
            []
            [ Options.styled
                p
                [ Typography.subhead ]
                [ icon
                , text title
                , location
                ]
            , Options.styled div [] (rows ++ activities)
            , Options.styled
                p
                [ Typography.caption, Options.css "margin-top" "1rem" ]
                [ text (translate lang CompanySource)
                , a [ href source, class "supplier-federal-revenue-source" ] [ text (translate lang CompanyFederalRevenue) ]
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
        case model.company of
            Just info ->
                viewCompany model.lang model.googleStreetViewApiKey info

            Nothing ->
                Options.styled div
                    [ Typography.caption ]
                    [ text "CNPJ invalid or not found." ]
    else if model.loading then
        Options.styled div
            [ Typography.caption ]
            [ text "Fetching company info from CNPJ…" ]
    else
        text ""
