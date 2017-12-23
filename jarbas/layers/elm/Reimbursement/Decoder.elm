module Reimbursement.Decoder exposing (..)

import Array exposing (Array, fromList)
import Dict
import Internationalization.Types exposing (Language)
import Json.Decode exposing (Decoder, array, bool, float, int, keyValuePairs, list, nullable, string)
import Json.Decode.Extra exposing (date)
import Json.Decode.Pipeline exposing (decode, hardcoded, required)
import Reimbursement.Company.Model as CompanyModel
import Reimbursement.Model exposing (Model, Reimbursement, Results, results)
import Reimbursement.Receipt.Decoder as ReceiptDecoder
import Reimbursement.Receipt.Model as ReceiptModel
import Reimbursement.RelatedTable.Model as RelatedTable
import String


{-| From a query list of key/values get the page number:

    getPage [ ( "page", "42" ), ( "year", "2016" ) ]
    --> Just 42

    getPage [ ( "page", "foo bar" ) ]
    --> Nothing

    getPage [ ( "format", "json" ) ]
    --> Nothing

-}
getPage : List ( String, String ) -> Maybe Int
getPage query =
    query
        |> Dict.fromList
        |> Dict.get "page"
        |> Maybe.andThen (String.toInt >> Result.toMaybe)


decoder : Language -> Maybe String -> List ( String, String ) -> Decoder Results
decoder lang apiKey query =
    let
        currentPage : Int
        currentPage =
            query
                |> getPage
                |> Maybe.withDefault 1
    in
        decode Results
            |> required "results" (array <| singleDecoder lang apiKey)
            |> required "count" (nullable int)
            |> required "previous" (nullable string)
            |> required "next" (nullable string)
            |> hardcoded Nothing
            |> hardcoded currentPage
            |> hardcoded (Just currentPage)


singleDecoder : Language -> Maybe String -> Decoder Reimbursement
singleDecoder lang apiKey =
    let
        supplier : CompanyModel.Model
        supplier =
            CompanyModel.model
    in
        decode Reimbursement
            |> required "year" int
            |> required "document_id" int
            |> required "applicant_id" int
            |> required "total_reimbursement_value" (nullable float)
            |> required "total_net_value" float
            |> required "all_reimbursement_numbers" (list int)
            |> required "all_net_values" (list float)
            |> required "congressperson_id" (nullable int)
            |> required "congressperson_name" (nullable string)
            |> required "congressperson_document" (nullable int)
            |> required "state" (nullable string)
            |> required "party" (nullable string)
            |> required "term_id" (nullable int)
            |> required "term" int
            |> required "subquota_id" int
            |> required "subquota_description" string
            |> required "subquota_group_id" (nullable int)
            |> required "subquota_group_description" (nullable string)
            |> required "supplier" string
            |> required "cnpj_cpf" (nullable string)
            |> required "document_type" int
            |> required "document_number" (nullable string)
            |> required "document_value" float
            |> required "issue_date" date
            |> required "month" int
            |> required "remark_value" (nullable float)
            |> required "installment" (nullable int)
            |> required "batch_number" (nullable int)
            |> required "all_reimbursement_values" (nullable <| list float)
            |> required "passenger" (nullable string)
            |> required "leg_of_the_trip" (nullable string)
            |> required "probability" (nullable float)
            |> required "suspicions" (nullable <| keyValuePairs bool)
            |> required "rosies_tweet" (nullable string)
            |> required "receipt" (ReceiptDecoder.decoder lang)
            |> hardcoded { supplier | googleStreetViewApiKey = apiKey }
            |> hardcoded RelatedTable.model
            |> hardcoded RelatedTable.model
            |> required "available_in_latest_dataset" bool


updateReimbursementLanguage : Language -> Reimbursement -> Reimbursement
updateReimbursementLanguage lang reimbursement =
    let
        receipt : ReceiptModel.Model
        receipt =
            reimbursement.receipt

        newReceipt : ReceiptModel.Model
        newReceipt =
            { receipt | lang = lang }

        supplier : CompanyModel.Model
        supplier =
            reimbursement.supplierInfo

        newCompany : CompanyModel.Model
        newCompany =
            { supplier | lang = lang }
    in
        { reimbursement | receipt = newReceipt, supplierInfo = newCompany }


updateLanguage : Language -> Model -> Model
updateLanguage lang model =
    let
        results : Results
        results =
            model.results

        newReimbursements : Array Reimbursement
        newReimbursements =
            Array.map (updateReimbursementLanguage lang) model.results.reimbursements

        newResults : Results
        newResults =
            { results | reimbursements = newReimbursements }
    in
        { model | lang = lang, results = newResults }


updateGoogleStreetViewApiKey : Maybe String -> Model -> Model
updateGoogleStreetViewApiKey key model =
    { model | googleStreetViewApiKey = key }
