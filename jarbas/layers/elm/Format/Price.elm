module Format.Price exposing (..)

import FormatNumber exposing (Locale, formatFloat)
import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..))
import String


formatPrice : Language -> Float -> String
formatPrice lang price =
    let
        locale : Locale
        locale =
            Locale
                2
                (translate lang ThousandSeparator)
                (translate lang DecimalSeparator)
    in
        formatFloat locale price
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
