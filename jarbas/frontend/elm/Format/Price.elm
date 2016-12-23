module Format.Price exposing (..)

import Format.Number exposing (formatNumber)
import Internationalization exposing (Language, TranslationId(..), translate)
import String


formatPrice : Language -> Float -> String
formatPrice lang price =
    formatNumber
        2
        (translate lang ThousandSeparator)
        (translate lang DecimalSeparator)
        price
        |> BrazilianCurrency
        |> translate lang


formatPrices : Language -> List Float -> String
formatPrices lang prices =
    List.map (formatPrice lang) prices
        |> String.join ", "


maybeFormatPrice : Language -> Maybe Float -> String
maybeFormatPrice lang maybePrice =
    case maybePrice of
        Just price ->
            formatPrice lang price

        Nothing ->
            ""


maybeFormatPrices : Language -> Maybe (List Float) -> String
maybeFormatPrices lang maybePrices =
    case maybePrices of
        Just prices ->
            formatPrices lang prices

        Nothing ->
            ""
