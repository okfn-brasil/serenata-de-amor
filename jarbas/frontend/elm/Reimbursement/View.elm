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
import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..))
import Material.Button as Button
import Material.Color as Color
import Material.Grid exposing (Device(..), cell, grid, size)
import Material.Icon as Icon
import Material.List as List
import Material.Options as Options
import Material.Textfield as Textfield
import Material.Typography as Typography
import Reimbursement.Company.View as CompanyView
import Reimbursement.Fields as Fields exposing (Field(..), Label(..), getLabelTranslation)
import Reimbursement.Map.Model as MapModel
import Reimbursement.Map.View as MapView
import Reimbursement.Model exposing (Model, Reimbursement, Results, results)
import Reimbursement.Receipt.View as ReceiptView
import Reimbursement.SameDay.View as SameDay
import Reimbursement.SameSubquota.View as SameSubquota
import Reimbursement.Search.Update as SearchUpdate
import Reimbursement.Search.View as SearchView
import Reimbursement.Tweet.Model as TweetModel
import Reimbursement.Tweet.View as TweetView
import Reimbursement.Update exposing (Msg(..), onlyDigits, totalPages)
import String


--
-- Pagination
--


{-| Adjust the width of the jump to page field:

    jumpToWidth "8" --> "1.618em"

    jumpToWidth "42" --> "2em"

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
            Textfield.render Mdl
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
        form [ onSubmit (Page model.results.jumpTo) ]
            [ PaginationPage |> translate model.lang |> text
            , input
            , PaginationOf |> translate model.lang |> text
            , total |> toString |> text
            ]


viewPaginationButton : Model -> Int -> Int -> String -> Html Msg
viewPaginationButton model page index icon =
    div []
        [ Button.render Mdl
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
            [ cell [ size Desktop 4, size Tablet 2, size Phone 1 ]
                [ Options.styled div
                    [ Typography.right ]
                    [ previous ]
                ]
            , cell [ size Desktop 4, size Tablet 4, size Phone 2 ]
                [ Options.styled div
                    [ Typography.center ]
                    [ viewJumpTo model ]
                ]
            , cell [ size Desktop 4, size Tablet 2, size Phone 1 ]
                [ Options.styled div
                    [ Typography.left ]
                    [ next ]
                ]
            ]



--
-- Reimbursements
--


sourceUrl : Reimbursement -> String
sourceUrl reimbursement =
    url "http://www.camara.gov.br/cota-parlamentar/documento"
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

    viewMaybeIntButZero ( Just 42 ) --> "42"

    viewMaybeIntButZero ( Just 0 ) --> ""

    viewMaybeIntButZero Nothing --> ""

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
            Options.styled p
                [ Typography.title ]
                [ text (translate lang ReimbursementNotFound) ]

        Nothing ->
            text ""


viewReimbursementBlockLine : Language -> Field -> Html Msg
viewReimbursementBlockLine lang field =
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
            [ Options.styled span (Typography.body2 :: labelStyles) [ text <| Fields.getLabelTranslation lang field ]
            , Options.styled span (Typography.body1 :: styles) [ text <| Fields.getValue field ]
            ]


viewSummaryPs : Language -> Reimbursement -> Html Msg
viewSummaryPs lang reimbursement =
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
                Options.styled p
                    [ Typography.caption ]
                    [ translate lang FieldsetCurrencyDetails |> text
                    , a [ href currencyUrl, target "_blank", class "currency" ]
                        [ translate lang FieldsetCurrencyDetailsLink |> text
                        , formatDate lang reimbursement.issueDate |> text
                        ]
                    , text "."
                    ]
            else
                text ""
    in
        div []
            [ currency
            , Options.styled p
                [ Typography.caption ]
                [ text (translate lang FieldsetCompanyDetails) ]
            ]


viewCongresspersonPs : Language -> Reimbursement -> Html Msg
viewCongresspersonPs lang reimbursement =
    let
        congresspersonUrl =
            url "http://www.camara.leg.br/Internet/Deputado/dep_Detalhe.asp"
                [ ( "id", viewMaybeIntButZero reimbursement.congresspersonId ) ]

        congresspersonLink =
            a [ href congresspersonUrl ]
                [ text (translate lang FieldsetCongresspersonProfile) ]
    in
        div []
            [ Options.styled p
                [ Typography.caption, Options.css "margin-top" "1rem" ]
                [ congresspersonLink ]
            ]


viewReimbursementBlock : Language -> Reimbursement -> ( String, String, List Field ) -> Html Msg
viewReimbursementBlock lang reimbursement ( title, icon, fields ) =
    let
        iconTag =
            Icon.view icon [ Options.css "transform" "translateY(0.4rem)" ]

        ps =
            if title == (translate lang FieldsetSummary) then
                viewSummaryPs lang reimbursement
            else if title == (translate lang FieldsetCongressperson) then
                viewCongresspersonPs lang reimbursement
            else
                text ""
    in
        div []
            [ Options.styled p
                [ Typography.subhead ]
                [ iconTag, text (" " ++ title) ]
            , List.ul [] (List.map (viewReimbursementBlockLine lang) fields)
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
            [ Field Congressperson <| congressperson
            , Field IssueDate <| formatDate lang reimbursement.issueDate
            , Field ClaimDate <| claimedDate
            , Field SubquotaDescription <| subquota
            , Field SubquotaGroupDescription <| Maybe.withDefault "" reimbursement.subquotaGroupDescription
            , Field Company <| viewCompany reimbursement
            , Field DocumentValue <| formatPrice lang reimbursement.documentValue
            , Field RemarkValue <| maybeFormatPrice lang reimbursement.remarkValue
            , Field TotalNetValue <| formatPrice lang reimbursement.totalNetValue
            , Field TotalReimbursementValue <| maybeFormatPrice lang reimbursement.totalReimbursementValue
            , Field Suspicions <| viewSuspicions lang reimbursement.suspicions
            ]
                |> List.filter (Fields.getValue >> String.isEmpty >> not)
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
            Internationalization.Types.DocumentType reimbursement.documentType
                |> translate lang

        fields =
            [ Field ApplicantId <| toString reimbursement.applicantId
            , Field DocumentId <| toString reimbursement.documentId
            , Field NetValues <| formatPrices lang reimbursement.netValues
            , Field ReimbursementValues <| maybeFormatPrices lang reimbursement.reimbursementValues
            , Field ReimbursementNumbers <| reimbursements
            , Field Fields.DocumentType <| documentType
            , Field DocumentNumber <| Maybe.withDefault "" reimbursement.documentNumber
            , Field Installment <| viewMaybeIntButZero reimbursement.installment
            , Field BatchNumber <| viewMaybeIntButZero reimbursement.batchNumber
            ]
                |> List.filter (Fields.getValue >> String.isEmpty >> not)
    in
        viewReimbursementBlock lang reimbursement ( translate lang FieldsetReimbursement, "folder", fields )


viewCongressPersonDetails : Language -> Reimbursement -> Html Msg
viewCongressPersonDetails lang reimbursement =
    let
        fields =
            [ Field CongresspersonId <| viewMaybeIntButZero reimbursement.congresspersonId
            , Field CongresspersonDocument <| viewMaybeIntButZero reimbursement.congresspersonDocument
            , Field Term <| toString reimbursement.term
            , Field TermId <| viewMaybeIntButZero reimbursement.termId
            ]
                |> List.filter (Fields.getValue >> String.isEmpty >> not)
    in
        viewReimbursementBlock lang reimbursement ( translate lang FieldsetCongressperson, "face", fields )


viewTrip : Language -> Reimbursement -> Html Msg
viewTrip lang reimbursement =
    let
        fields =
            [ Field Passenger <| Maybe.withDefault "" reimbursement.passenger
            , Field LegOfTheTrip <| Maybe.withDefault "" reimbursement.legOfTheTrip
            ]
                |> List.filter (Fields.getValue >> String.isEmpty >> not)
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
            reimbursement.receipt
                |> ReceiptView.view
                |> Html.map (ReceiptMsg index)

        tweet =
            reimbursement.tweet
                |> TweetModel.modelFrom lang
                |> TweetView.view
                |> Html.map (\_ -> TweetMsg)

        mapButton =
            reimbursement.supplierInfo
                |> MapModel.modelFrom lang
                |> MapView.view
                |> Html.map (\_ -> MapMsg)

        deletedTitle : Html Msg
        deletedTitle =
            if reimbursement.inLatestDataset then
                text ""
            else
                Options.styled p
                    [ Typography.caption ]
                    [ Icon.view "warning"
                        [ Options.css "transform" "translateY(0.3rem)"
                        , Options.css "margin-right" "0.25rem"
                        , Icon.size18
                        ]
                    , ReimbursementDeletedTitle |> translate lang |> text
                    ]

        title =
            Options.styled p
                [ Typography.headline, Color.text Color.primary ]
                [ (translate lang ReimbursementTitle) ++ (toString reimbursement.documentId) |> text ]

        supplier =
            CompanyView.view reimbursement.supplierInfo
                |> Html.map (CompanyMsg index)

        supplierTitle =
            Options.styled p
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

        reimbursementDeleted : Html Msg
        reimbursementDeleted =
            if reimbursement.inLatestDataset then
                text ""
            else
                ReimbursementDeletedSource
                    |> translate lang
                    |> text

        reimbursementSource : Html Msg
        reimbursementSource =
            Options.styled p
                [ Typography.caption, Options.css "margin-top" "1rem" ]
                [ text (translate lang ReimbursementSource)
                , a [ href (sourceUrl reimbursement), class "chamber-of-deputies-source" ]
                    [ text (translate lang ReimbursementChamberOfDeputies) ]
                , reimbursementDeleted
                ]
    in
        [ cell [ size Desktop 6, size Tablet 4, size Phone 2 ]
            [ Options.styled div [ Options.css "margin-top" "3rem" ] [ title, deletedTitle ] ]
        , cell [ size Desktop 6, size Tablet 4, size Phone 2 ]
            [ Options.styled div
                [ Options.css "margin-top" "3rem", Typography.right ]
                [ tweet, receipt, mapButton ]
            ]
        , cell [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] blocks
            , reimbursementSource
            , sameDay
            , sameSubquota
            ]
        , cell [ size Desktop 6, size Tablet 8, size Phone 4 ]
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
            SearchUpdate.toUrl model.searchFields |> String.isEmpty |> not

        results : String
        results =
            if total == 1 then
                (toString total) ++ (translate model.lang ResultTitleSingular)
            else
                (toString total) ++ (translate model.lang ResultTitlePlural)

        title : Material.Grid.Cell Msg
        title =
            cell [ size Desktop 12, size Tablet 8, size Phone 4 ]
                [ Options.styled div
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
        [ SearchView.view model
        , viewReimbursements model
        ]
