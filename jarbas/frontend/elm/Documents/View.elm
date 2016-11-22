module Documents.View exposing (..)

import Documents.Fields as Fields
import Documents.Inputs.View as InputsView
import Documents.Inputs.Update as InputsUpdate
import Documents.Map.View as MapView
import Documents.Map.Model as MapModel
import Documents.Receipt.View as ReceiptView
import Documents.Supplier as Supplier
import Html exposing (a, div, form, p, span, text)
import Html.App
import Html.Attributes exposing (href)
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
import Documents.Model exposing (Model, Document, Results, results)
import Documents.Update exposing (Msg(..), onlyDigits, totalPages)


--
-- View
--
-- Form


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
            InputsView.view model.loading model.inputs |> Html.App.map InputsMsg

        send =
            viewButton
                model
                0
                [ Button.raised, Button.colored, Button.type' "submit" ]
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



-- Pagination


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



-- Documents


sourceUrl : Document -> String
sourceUrl document =
    Http.url
        "http://www.camara.gov.br/cota-parlamentar/documento"
        [ ( "nuDeputadoId", toString document.applicant_id )
        , ( "numMes", toString document.month )
        , ( "numAno", toString document.year )
        , ( "despesa", toString document.subquota_number )
        , ( "cnpjFornecedor", document.cnpj_cpf )
        , ( "idDocumento", document.document_number )
        ]


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


viewDocumentBlock : Language -> ( String, String, List ( String, String ) ) -> Html.Html Msg
viewDocumentBlock lang ( title, icon, fields ) =
    let
        iconTag =
            Icon.view icon [ Options.css "transform" "translateY(0.4rem)" ]

        ps =
            if title == (translate lang FieldsetSupplier) then
                Options.styled
                    p
                    [ Typography.caption ]
                    [ text (translate lang FieldsetSupplierDetails) ]
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


viewDocument : Language -> Int -> Document -> List (Material.Grid.Cell Msg)
viewDocument lang index document =
    let
        getLabel =
            Fields.getLabel lang

        blocks =
            [ ( translate lang FieldsetCongressperson
              , "face"
              , [ ( getLabel "congressperson_name", document.congressperson_name )
                , ( getLabel "congressperson_id", toString document.congressperson_id )
                , ( getLabel "congressperson_document", toString document.congressperson_document )
                , ( getLabel "state", document.state )
                , ( getLabel "party", document.party )
                , ( getLabel "term", toString document.term )
                , ( getLabel "term_id", toString document.term_id )
                ]
              )
            , ( translate lang FieldsetSubquota
              , "list"
              , [ ( getLabel "subquota_number", toString document.subquota_number )
                , ( getLabel "subquota_description", document.subquota_description )
                , ( getLabel "subquota_group_id", toString document.subquota_group_id )
                , ( getLabel "subquota_group_description", document.subquota_group_description )
                ]
              )
            , ( translate lang FieldsetSupplier
              , "store"
              , [ ( getLabel "supplier", document.supplier )
                , ( getLabel "cnpj_cpf", document.cnpj_cpf )
                ]
              )
            , ( translate lang FieldsetDocument
              , "receipt"
              , [ ( getLabel "document_id", toString document.document_id )
                , ( getLabel "document_number", document.document_number )
                , ( getLabel "document_type", toString document.document_type )
                , ( getLabel "month", toString document.month )
                , ( getLabel "year", toString document.year )
                , ( getLabel "issue_date", Maybe.withDefault "" document.issue_date )
                ]
              )
            , ( translate lang FieldsetValues
              , "monetization_on"
              , [ ( getLabel "document_value", toString document.document_value )
                , ( getLabel "remark_value", toString document.remark_value )
                , ( getLabel "net_value", toString document.net_value )
                , ( getLabel "reimbursement_value", toString document.reimbursement_value )
                , ( getLabel "installment", toString document.installment )
                ]
              )
            , ( translate lang FieldsetTrip
              , "flight"
              , [ ( getLabel "passenger", document.passenger )
                , ( getLabel "leg_of_the_trip", document.leg_of_the_trip )
                ]
              )
            , ( translate lang FieldsetApplication
              , "folder"
              , [ ( getLabel "applicant_id", toString document.applicant_id )
                , ( getLabel "batch_number", toString document.batch_number )
                , ( getLabel "reimbursement_number", toString document.reimbursement_number )
                ]
              )
            ]

        receipt =
            Html.App.map (ReceiptMsg index) (ReceiptView.view document.id document.receipt)

        mapModel =
            MapModel.modelFrom lang document.supplier_info

        mapButton =
            Html.App.map (\_ -> MapMsg) <| MapView.view mapModel

        title =
            Options.styled
                p
                [ Typography.headline, Color.text Color.primary ]
                [ (translate lang DocumentTitle) ++ (toString document.document_id) |> text ]

        supplier =
            Html.App.map (SupplierMsg index) (Supplier.view document.supplier_info)

        supplierTitle =
            Options.styled
                p
                [ Typography.headline ]
                [ text "" ]
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
            [ Options.styled div [] (List.map (viewDocumentBlock lang) blocks)
            , Options.styled
                p
                [ Typography.caption, Options.css "margin-top" "1rem" ]
                [ text (translate lang DocumentSource)
                , a
                    [ href (sourceUrl document) ]
                    [ text (translate lang DocumentChamberOfDeputies) ]
                ]
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
                (translate model.lang ResultTitleSingular)
            else
                (translate model.lang ResultTitlePlural)

        title =
            cell
                [ size Desktop 12, size Tablet 8, size Phone 4 ]
                [ Options.styled
                    div
                    [ Typography.center, Typography.display1 ]
                    [ (toString total) ++ results |> text ]
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
