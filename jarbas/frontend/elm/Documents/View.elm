module Documents.View exposing (..)

import Date
import Date.Format
import Documents.Company.View as CompanyView
import Documents.Inputs.Update as InputsUpdate
import Documents.Inputs.View as InputsView
import Documents.Map.Model as MapModel
import Documents.Map.View as MapView
import Documents.Model exposing (Model, Document, Results, results)
import Documents.Receipt.View as ReceiptView
import Documents.SameDay.View as SameDay
import Documents.Update exposing (Msg(..), onlyDigits, totalPages)
import Format.CnpjCpf exposing (formatCnpjCpf)
import Format.Price exposing (..)
import Format.Url exposing (url)
import Html exposing (a, div, form, p, span, text)
import Html.Attributes exposing (class, href, target)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material.Button as Button
import Material.Color as Color
import Material.Grid exposing (grid, cell, size, Device(..))
import Material.Icon as Icon
import Material.List as List
import Material.Options as Options
import Material.Textfield as Textfield
import Material.Typography as Typography
import String


--
-- Form
--


viewButton : Model -> Int -> List (Button.Property Msg) -> TranslationId -> Html.Html Msg
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


viewForm : Model -> Html.Html Msg
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


viewJumpTo : Model -> Html.Html Msg
viewJumpTo model =
    let
        cleaned =
            onlyDigits model.results.jumpTo

        input =
            Textfield.render
                Mdl
                [ 0 ]
                model.mdl
                [ Textfield.onInput Update
                , Textfield.value cleaned
                , Options.css "width" (jumpToWidth cleaned)
                , Textfield.style [ (Options.css "text-align" "center") ]
                ]

        page =
            Result.withDefault 0 (String.toInt model.results.jumpTo)

        total =
            Maybe.withDefault 0 model.results.total |> totalPages
    in
        form
            [ onSubmit (Page page) ]
            [ text (translate model.lang PaginationPage)
            , input
            , text (translate model.lang PaginationOf)
            , text (toString total)
            ]


viewPaginationButton : Model -> Int -> Int -> String -> Html.Html Msg
viewPaginationButton model page index icon =
    div
        []
        [ Button.render
            Mdl
            [ index ]
            model.mdl
            [ Button.minifab
            , Button.onClick <| Page page
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
-- Documents
--


sourceUrl : Document -> String
sourceUrl document =
    url
        "http://www.camara.gov.br/cota-parlamentar/documento"
        [ ( "nuDeputadoId", toString document.applicantId )
        , ( "numMes", toString document.month )
        , ( "numAno", toString document.year )
        , ( "despesa", toString document.subquotaId )
        , ( "cnpjFornecedor", Maybe.withDefault "" document.cnpjCpf )
        , ( "idDocumento", Maybe.withDefault "" document.documentNumber )
        ]


viewDate : Language -> Date.Date -> String
viewDate lang date =
    FormattedDate date |> translate lang


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


viewCompany : Document -> String
viewCompany document =
    case document.cnpjCpf of
        Just value ->
            String.concat
                [ document.supplier
                , " ("
                , formatCnpjCpf value
                , ")"
                ]

        Nothing ->
            document.supplier


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


viewError : Language -> Maybe Http.Error -> Html.Html Msg
viewError lang error =
    case error of
        Just _ ->
            Options.styled
                p
                [ Typography.title ]
                [ text (translate lang DocumentNotFound) ]

        Nothing ->
            text ""


viewDocumentBlockLine : ( String, String ) -> Html.Html Msg
viewDocumentBlockLine ( label, value ) =
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


viewPs : Language -> Document -> Html.Html Msg
viewPs lang document =
    let
        currencyUrl =
            String.concat
                [ "http://x-rates.com/historical/?from=BRL&amount="
                , toString document.totalNetValue
                , "&date="
                , Date.Format.format "%Y-%m-%d" document.issueDate
                ]

        currency =
            if document.documentType == 2 then
                Options.styled
                    p
                    [ Typography.caption ]
                    [ translate lang FieldsetCurrencyDetails |> text
                    , a
                        [ href currencyUrl, target "_blank", class "currency" ]
                        [ translate lang FieldsetCurrencyDetailsLink |> text
                        , viewDate lang document.issueDate |> text
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


viewDocumentBlock : Language -> Document -> ( String, String, List ( String, String ) ) -> Html.Html Msg
viewDocumentBlock lang document ( title, icon, fields ) =
    let
        iconTag =
            Icon.view icon [ Options.css "transform" "translateY(0.4rem)" ]

        ps =
            if title == (translate lang FieldsetSummary) then
                viewPs lang document
            else
                text ""
    in
        div
            []
            [ Options.styled
                p
                [ Typography.subhead ]
                [ iconTag, text (" " ++ title) ]
            , List.ul [] (List.map viewDocumentBlockLine fields)
            , ps
            ]


viewSummaryBlock : Language -> Document -> Html.Html Msg
viewSummaryBlock lang document =
    let
        congressperson =
            String.concat
                [ Maybe.withDefault "" document.congresspersonName
                , " ("
                , Maybe.withDefault "" document.party
                , "/"
                , Maybe.withDefault "" document.state
                , ")"
                ]

        claimedDate =
            [ document.month, document.year ]
                |> List.map toString
                |> String.join "/"

        subquota =
            String.concat
                [ document.subquotaDescription
                , " ("
                , toString document.subquotaId
                , ")"
                ]

        fields =
            [ ( translate lang FieldCongressperson, congressperson )
            , ( translate lang FieldIssueDate, viewDate lang document.issueDate )
            , ( translate lang FieldClaimDate, claimedDate )
            , ( translate lang FieldSubquotaDescription, subquota )
            , ( translate lang FieldSubquotaGroupDescription, Maybe.withDefault "" document.subquotaGroupDescription )
            , ( translate lang FieldCompany, viewCompany document )
            , ( translate lang FieldDocumentValue, formatPrice lang document.documentValue )
            , ( translate lang FieldRemarkValue, maybeFormatPrice lang document.remarkValue )
            , ( translate lang FieldTotalNetValue, formatPrice lang document.totalNetValue )
            , ( translate lang FieldTotalReimbursementValue, maybeFormatPrice lang document.totalReimbursementValue )
            , ( translate lang FieldSuspicions, viewSuspicions lang document.suspicions )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        viewDocumentBlock lang document ( translate lang FieldsetSummary, "list", fields )


viewReimbursementDetails : Language -> Document -> Html.Html Msg
viewReimbursementDetails lang document =
    let
        reimbursements =
            document.reimbursementNumbers
                |> List.map toString
                |> String.join ", "

        documentType =
            DocumentType document.documentType
                |> translate lang

        fields =
            [ ( translate lang FieldApplicantId, toString document.applicantId )
            , ( translate lang FieldDocumentId, toString document.documentId )
            , ( translate lang FieldNetValues, formatPrices lang document.netValues )
            , ( translate lang FieldReimbursementValues, maybeFormatPrices lang document.reimbursementValues )
            , ( translate lang FieldReimbursementNumbers, reimbursements )
            , ( translate lang FieldDocumentType, documentType )
            , ( translate lang FieldDocumentNumber, Maybe.withDefault "" document.documentNumber )
            , ( translate lang FieldInstallment, viewMaybeIntButZero document.installment )
            , ( translate lang FieldBatchNumber, viewMaybeIntButZero document.batchNumber )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        viewDocumentBlock lang document ( translate lang FieldsetReimbursement, "folder", fields )


viewCongressPersonDetails : Language -> Document -> Html.Html Msg
viewCongressPersonDetails lang document =
    let
        fields =
            [ ( translate lang FieldCongresspersonId, viewMaybeIntButZero document.congresspersonId )
            , ( translate lang FieldCongresspersonDocument, viewMaybeIntButZero document.congresspersonDocument )
            , ( translate lang FieldTerm, toString document.term )
            , ( translate lang FieldTermId, toString document.termId )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        viewDocumentBlock lang document ( translate lang FieldsetCongressperson, "face", fields )


viewTrip : Language -> Document -> Html.Html Msg
viewTrip lang document =
    let
        fields =
            [ ( translate lang FieldPassenger, Maybe.withDefault "" document.passenger )
            , ( translate lang FieldLegOfTheTrip, Maybe.withDefault "" document.legOfTheTrip )
            ]
                |> List.filter (\( key, value ) -> String.isEmpty value |> not)
    in
        if List.isEmpty fields then
            text ""
        else
            viewDocumentBlock lang document ( translate lang FieldsetTrip, "flight", fields )


viewDocument : Language -> Int -> Document -> List (Material.Grid.Cell Msg)
viewDocument lang index document =
    let
        blocks =
            [ viewSummaryBlock lang document
            , viewTrip lang document
            , viewReimbursementDetails lang document
            , viewCongressPersonDetails lang document
            ]

        receipt =
            ReceiptView.view document.receipt
                |> Html.map (ReceiptMsg index)

        mapModel =
            MapModel.modelFrom lang document.supplierInfo

        mapButton =
            MapView.view mapModel
                |> Html.map (\_ -> MapMsg)

        title =
            Options.styled
                p
                [ Typography.headline, Color.text Color.primary ]
                [ (translate lang DocumentTitle) ++ (toString document.documentId) |> text ]

        supplier =
            CompanyView.view document.supplierInfo
                |> Html.map (CompanyMsg index)

        supplierTitle =
            Options.styled
                p
                [ Typography.headline ]
                [ text "" ]

        sameDay : Html.Html Msg
        sameDay =
            SameDay.view document.sameDay
                |> Html.map (SameDayMsg index)
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
                [ text (translate lang DocumentSource)
                , a
                    [ href (sourceUrl document), class "chamber-of-deputies-source" ]
                    [ text (translate lang DocumentChamberOfDeputies) ]
                ]
            , sameDay
            ]
        , cell
            [ size Desktop 6, size Tablet 8, size Phone 4 ]
            [ Options.styled div [] [ supplierTitle, supplier ] ]
        ]


viewDocuments : Model -> Html.Html Msg
viewDocuments model =
    let
        documents =
            List.concat <|
                List.indexedMap
                    (\idx doc -> (viewDocument model.lang idx doc))
                    model.results.documents

        total =
            Maybe.withDefault 0 model.results.total

        searched =
            InputsUpdate.toQuery model.inputs |> List.isEmpty |> not

        results =
            if total == 1 then
                (toString total) ++ (translate model.lang ResultTitleSingular)
            else
                (toString total) ++ (translate model.lang ResultTitlePlural)

        title =
            cell
                [ size Desktop 12, size Tablet 8, size Phone 4 ]
                [ Options.styled
                    div
                    [ Typography.center, Typography.display1 ]
                    [ results |> text ]
                ]

        pagination =
            viewPagination model

        cells =
            List.concat [ pagination, documents, pagination ]
    in
        if model.loading then
            text ""
        else if searched then
            grid [] (title :: cells)
        else
            grid [] cells



--


view : Model -> Html.Html Msg
view model =
    div []
        [ viewForm model
        , viewDocuments model
        ]
