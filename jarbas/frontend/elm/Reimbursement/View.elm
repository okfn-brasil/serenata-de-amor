module Reimbursement.View exposing (..)

import Array
import Date.Extra.Format exposing (utcIsoDateString)
import Format.CnpjCpf exposing (formatCnpjCpf)
import Format.Date exposing (formatDate)
import Format.Price exposing (..)
import Format.Url exposing (url)
import Html exposing (Html, a, div, form, p, span, text)
import Html.Attributes exposing (class, href, target)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material.Button as Button
import Material.Color as Color
import Material.Grid exposing (Device(..), cell, grid, size)
import Material.Icon as Icon
import Material.List as List
import Material.Options as Options
import Material.Textfield as Textfield
import Material.Typography as Typography
import Reimbursement.Company.View as CompanyView
import Reimbursement.Inputs.Update as InputsUpdate
import Reimbursement.Inputs.View as InputsView
import Reimbursement.Map.Model as MapModel
import Reimbursement.Map.View as MapView
import Reimbursement.Model exposing (Model, Reimbursement, Results, results)
import Reimbursement.Receipt.View as ReceiptView
import Reimbursement.SameDay.View as SameDay
import Reimbursement.SameSubquota.View as SameSubquota
import Reimbursement.Update exposing (Msg(..), onlyDigits, totalPages)
import String


--
-- Form
--


viewButton : Model -> Int -> List (Button.Property Msg) -> TranslationId -> Html Msg
viewButton model index defaultAttr defaultLabel =
    let
        label =
            if model.loading then
                translate model.lang Loading
            else
                translate model.lang defaultLabel

        attr =
            if model.loading then
                Button.disabled :: defaultAttr
            else
                defaultAttr
    in
        grid
            []
            [ cell
                [ size Desktop 12, size Tablet 8, size Phone 4 ]
                [ Options.styled
                    div
                    [ Typography.center ]
                    [ Button.render
                        Mdl
                        [ index ]
                        model.mdl
                        attr
                        [ text label ]
                    ]
                ]
            ]


viewForm : Model -> Html Msg
viewForm model =
    let
        inputs =
            InputsView.view model.loading model.inputs |> Html.map InputsMsg

        send =
            viewButton
                model
                0
                [ Button.raised, Button.colored, Button.type_ "submit" ]
                Search

        showForm =
            viewButton
                model
                1
                [ Button.raised, Button.onClick ToggleForm ]
                NewSearch
    in
        if model.showForm then
            form [ onSubmit Submit ] [ inputs, send ]
        else
            showForm



--
-- Pagination
--


{-| Adjust the width of the jump to page field:

    >>> jumpToWidth "8"
    "1.618em"

    >>> jumpToWidth "42"
    "2em"

-}
jumpToWidth : String -> String
jumpToWidth value =
    let
        actual =
            String.length value |> toFloat

        width =
            if actual <= 1.0 then
                1.618
            else
                actual
    in
        (toString width) ++ "em"


viewJumpTo : Model -> Html Msg
viewJumpTo model =
    let
        jumpTo : String
        jumpTo =
            model.results.jumpTo
                |> Maybe.map toString
                |> Maybe.withDefault ""

        input : Html Msg
        input =
            Textfield.render
                Mdl
                [ 0 ]
                model.mdl
                [ Textfield.onInput UpdateJumpTo
                , Textfield.onBlur RecoverJumpTo
                , Textfield.value jumpTo
                , jumpTo |> jumpToWidth |> Options.css "width"
                , Textfield.style [ (Options.css "text-align" "center") ]
                ]

        total : Int
        total =
            model.results.total
                |> Maybe.withDefault 1
                |> totalPages
    in
        form
            [ onSubmit (Page model.results.jumpTo) ]
            [ PaginationPage |> translate model.lang |> text
            , input
            , PaginationOf |> translate model.lang |> text
            , total |> toString |> text
            ]


viewPaginationButton : Model -> Int -> Int -> String -> Html Msg
viewPaginationButton model page index icon =
    div
        []
        [ Button.render
            Mdl
            [ index ]
            model.mdl
            [ Button.minifab
            , page |> Just |> Page |> Button.onClick
            ]
            [ Icon.i icon ]
        ]


viewPagination : Model -> List (Material.Grid.Cell Msg)
viewPagination model =
    let
        current =
            model.results.pageLoaded

        total =
            Maybe.withDefault 0 model.results.total |> totalPages

        previous =
            case model.results.previous of
                Just url ->
                    viewPaginationButton model (current - 1) 1 "chevron_left"

                Nothing ->
                    text ""

        next =
            case model.results.next of
                Just url ->
                    viewPaginationButton model (current + 1) 2 "chevron_right"

                Nothing ->
                    text ""
    in
        if current >= total then
            []
        else
            [ cell
                [ size Desktop 4, size Tablet 2, size Phone 1 ]
                [ Options.styled
                    div
                    [ Typography.right ]
                    [ previous ]
                ]
            , cell
                [ size Desktop 4, size Tablet 4, size Phone 2 ]
                [ Options.styled
                    div
                    [ Typography.center ]
                    [ viewJumpTo model ]
                ]
            , cell
                [ size Desktop 4, size Tablet 2, size Phone 1 ]
                [ Options.styled
                    div
                    [ Typography.left ]
                    [ next ]
                ]
            ]



--
-- Reimbursements
--


sourceUrl : Reimbursement -> String
sourceUrl reimbursement =
    url
        "http://www.camara.gov.br/cota-parlamentar/documento"
        [ ( "nuDeputadoId", toString reimbursement.applicantId )
        , ( "numMes", toString reimbursement.month )
        , ( "numAno", toString reimbursement.year )
        , ( "despesa", toString reimbursement.subquotaId )
        , ( "cnpjFornecedor", Maybe.withDefault "" reimbursement.cnpjCpf )
        , ( "idDocumento", Maybe.withDefault "" reimbursement.documentNumber )
        ]


viewSuspicions : Language -> Maybe (List ( String, Bool )) -> String
viewSuspicions lang maybeSuspicions =
    case maybeSuspicions of
        Just suspicions ->
            suspicions
                |> List.filter (\( key, value ) -> value)
                |> List.map (\( key, value ) -> translate lang <| Suspicion key)
                |> String.join ", "

        Nothing ->
            ""


viewCompany : Reimbursement -> String
viewCompany reimbursement =
    case reimbursement.cnpjCpf of
        Just value ->
            String.concat
                [ reimbursement.supplier
                , " ("
                , formatCnpjCpf value
                , ")"
                ]

        Nothing ->
            reimbursement.supplier


{-| Convert a Maybe Int to String except if it's zero:

    >>> viewMaybeIntButZero ( Just 42 )
    "42"

    >>> viewMaybeIntButZero ( Just 0 )
    ""

    >>> viewMaybeIntButZero Nothing
    ""

-}
viewMaybeIntButZero : Maybe Int -> String
viewMaybeIntButZero maybeInt =
    case maybeInt of
        Just int ->
            if int == 0 then
                ""
            else
                toString int

        Nothing ->
            ""


viewError : Language -> Maybe Http.Error -> Html Msg
viewError lang error =
    case error of
        Just _ ->
            Options.styled
                p
                [ Typography.title ]
                [ text (translate lang ReimbursementNotFound) ]

        Nothing ->
            text ""


viewReimbursementBlockLine : ( String, String ) -> Html Msg
viewReimbursementBlockLine ( label, value ) =
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


viewPs : Language -> Reimbursement -> Html Msg
viewPs lang reimbursement =
    let
        currencyUrl =
            String.concat
                [ "http://x-rates.com/historical/?from=BRL&amount="
                , toString reimbursement.totalNetValue
                , "&date="
                , utcIsoDateString reimbursement.issueDate
                ]

        currency =
            if reimbursement.documentType == 2 then
                Options.styled
                    p
                    [ Typography.caption ]
                    [ translate lang FieldsetCurrencyDetails |> text
                    , a
                        [ href currencyUrl, target "_blank", class "currency" ]
                        [ translate lang FieldsetCurrencyDetailsLink |> text
                        , formatDate lang reimbursement.issueDate |> text
                        ]
                    , text "."
                    ]
            else
                text ""
    in
        div
            []
            [ currency
            , Options.styled
                p
                [ Typography.caption ]
                [ text (translate lang FieldsetCompanyDetails) ]
            ]


viewReimbursementBlock : Language -> Reimbursement -> ( String, String, List ( String, String ) ) -> Html Msg
viewReimbursementBlock lang reimbursement ( title, icon, fields ) =
    let
        iconTag =
            Icon.view icon [ Options.css "transform" "translateY(0.4rem)" ]

        ps =
            if title == (translate lang FieldsetSummary) then
                viewPs lang reimbursement
            else
                text ""
    in
        div
            []
            [ Options.styled
                p
                [ Typography.subhead ]
                [ iconTag, text (" " ++ title) ]
            , List.ul [] (List.map viewReimbursementBlockLine fields)
            , ps
            ]


viewSummaryBlock : Language -> Reimbursement -> Html Msg
viewSummaryBlock lang reimbursement =
    let
        congressperson =
            String.concat
                [ Maybe.withDefault "" reimbursement.congresspersonName
                , " ("
                , Maybe.withDefault "" reimbursement.party
                , "/"
                , Maybe.withDefault "" reimbursement.state
                , ")"
                ]

        claimedDate =
            [ reimbursement.month, reimbursement.year ]
                |> List.map toString
                |> String.join "/"

        subquota =
            String.concat
                [ reimbursement.subquotaDescription
                , " ("
                , toString reimbursement.subquotaId
                , ")"
                ]

        fields =
            [ ( translate lang FieldCongressperson, congressperson )
            , ( translate lang FieldIssueDate, formatDate lang reimbursement.issueDate )
            , ( translate lang FieldClaimDate, claimedDate )
            , ( translate lang FieldSubquotaDescription, subquota )
            , ( translate lang FieldSubquotaGroupDescription, Maybe.withDefault "" reimbursement.subquotaGroupDescription )
            , ( translate lang FieldCompany, viewCompany reimbursement )
            , ( translate lang FieldDocumentValue, formatPrice lang reimbursement.documentValue )
            , ( translate lang FieldRemarkValue, maybeFormatPrice lang reimbursement.remarkValue )
            , ( translate lang FieldTotalNetValue, formatPrice lang reimbursement.totalNetValue )
            , ( translate lang FieldTotalReimbursementValue, maybeFormatPrice lang reimbursement.totalReimbursementValue )
            , ( translate lang FieldSuspicions, viewSuspicions lang reimbursement.suspicions )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        viewReimbursementBlock lang reimbursement ( translate lang FieldsetSummary, "list", fields )


viewReimbursementDetails : Language -> Reimbursement -> Html Msg
viewReimbursementDetails lang reimbursement =
    let
        reimbursements =
            reimbursement.reimbursementNumbers
                |> List.map toString
                |> String.join ", "

        documentType =
            DocumentType reimbursement.documentType
                |> translate lang

        fields =
            [ ( translate lang FieldApplicantId, toString reimbursement.applicantId )
            , ( translate lang FieldDocumentId, toString reimbursement.documentId )
            , ( translate lang FieldNetValues, formatPrices lang reimbursement.netValues )
            , ( translate lang FieldReimbursementValues, maybeFormatPrices lang reimbursement.reimbursementValues )
            , ( translate lang FieldReimbursementNumbers, reimbursements )
            , ( translate lang FieldDocumentType, documentType )
            , ( translate lang FieldDocumentNumber, Maybe.withDefault "" reimbursement.documentNumber )
            , ( translate lang FieldInstallment, viewMaybeIntButZero reimbursement.installment )
            , ( translate lang FieldBatchNumber, viewMaybeIntButZero reimbursement.batchNumber )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        viewReimbursementBlock lang reimbursement ( translate lang FieldsetReimbursement, "folder", fields )


viewCongressPersonDetails : Language -> Reimbursement -> Html Msg
viewCongressPersonDetails lang reimbursement =
    let
        fields =
            [ ( translate lang FieldCongresspersonId, viewMaybeIntButZero reimbursement.congresspersonId )
            , ( translate lang FieldCongresspersonDocument, viewMaybeIntButZero reimbursement.congresspersonDocument )
            , ( translate lang FieldTerm, toString reimbursement.term )
            , ( translate lang FieldTermId, viewMaybeIntButZero reimbursement.termId )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        viewReimbursementBlock lang reimbursement ( translate lang FieldsetCongressperson, "face", fields )


viewTrip : Language -> Reimbursement -> Html Msg
viewTrip lang reimbursement =
    let
        fields =
            [ ( translate lang FieldPassenger, Maybe.withDefault "" reimbursement.passenger )
            , ( translate lang FieldLegOfTheTrip, Maybe.withDefault "" reimbursement.legOfTheTrip )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        if List.isEmpty fields then
            text ""
        else
            viewReimbursementBlock lang reimbursement ( translate lang FieldsetTrip, "flight", fields )


viewReimbursement : Language -> Int -> Reimbursement -> List (Material.Grid.Cell Msg)
viewReimbursement lang index reimbursement =
    let
        blocks =
            [ viewSummaryBlock lang reimbursement
            , viewTrip lang reimbursement
            , viewReimbursementDetails lang reimbursement
            , viewCongressPersonDetails lang reimbursement
            ]

        receipt =
            ReceiptView.view reimbursement.receipt
                |> Html.map (ReceiptMsg index)

        mapModel =
            MapModel.modelFrom lang reimbursement.supplierInfo

        mapButton =
            MapView.view mapModel
                |> Html.map (\_ -> MapMsg)

        title =
            Options.styled
                p
                [ Typography.headline, Color.text Color.primary ]
                [ (translate lang ReimbursementTitle) ++ (toString reimbursement.documentId) |> text ]

        supplier =
            CompanyView.view reimbursement.supplierInfo
                |> Html.map (CompanyMsg index)

        supplierTitle =
            Options.styled
                p
                [ Typography.headline ]
                [ text "" ]

        sameDay : Html Msg
        sameDay =
            SameDay.view reimbursement.sameDay
                |> Html.map (SameDayMsg index)

        sameSubquota : Html Msg
        sameSubquota =
            SameSubquota.view reimbursement.sameSubquota
                |> Html.map (SameSubquotaMsg index)
    in
        [ cell
            [ size Desktop 6, size Tablet 4, size Phone 2 ]
            [ Options.styled div [ Options.css "margin-top" "3rem" ] [ title ] ]
        , cell
            [ size Desktop 6, size Tablet 4, size Phone 2 ]
            [ Options.styled
                div
                [ Options.css "margin-top" "3rem", Typography.right ]
                [ receipt, mapButton ]
            ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] blocks
            , Options.styled
                p
                [ Typography.caption, Options.css "margin-top" "1rem" ]
                [ text (translate lang ReimbursementSource)
                , a
                    [ href (sourceUrl reimbursement), class "chamber-of-deputies-source" ]
                    [ text (translate lang ReimbursementChamberOfDeputies) ]
                ]
            , sameDay
            , sameSubquota
            ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] [ supplierTitle, supplier ] ]
        ]


viewReimbursements : Model -> Html Msg
viewReimbursements model =
    let
        reimbursements : List (Material.Grid.Cell Msg)
        reimbursements =
            model.results.reimbursements
                |> Array.toIndexedList
                |> List.map (\( idx, reimb ) -> viewReimbursement model.lang idx reimb)
                |> List.concat

        total : Int
        total =
            Maybe.withDefault 0 model.results.total

        searched : Bool
        searched =
            InputsUpdate.toQuery model.inputs |> List.isEmpty |> not

        results : String
        results =
            if total == 1 then
                (toString total) ++ (translate model.lang ResultTitleSingular)
            else
                (toString total) ++ (translate model.lang ResultTitlePlural)

        title : Material.Grid.Cell Msg
        title =
            cell
                [ size Desktop 12, size Tablet 8, size Phone 4 ]
                [ Options.styled
                    div
                    [ Typography.center, Typography.display1 ]
                    [ results |> text ]
                ]

        pagination : List (Material.Grid.Cell Msg)
        pagination =
            viewPagination model

        cells : List (Material.Grid.Cell Msg)
        cells =
            List.concat [ pagination, reimbursements, pagination ]
    in
        if model.loading then
            text ""
        else if searched then
            grid [] (title :: cells)
        else
            grid [] cells



--


view : Model -> Html Msg
view model =
    div []
        [ viewForm model
        , viewReimbursements model
        ]
