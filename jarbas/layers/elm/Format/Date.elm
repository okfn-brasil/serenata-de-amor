module Format.Date exposing (formatDate)

import Date
import Date.Extra.Config.Config_en_us as Config_en_us
import Date.Extra.Config.Config_pt_br as Config_pt_br
import Date.Extra.Format exposing (formatUtc)
import Internationalization.Types exposing (Language(..))


formatDate : Language -> Date.Date -> String
formatDate lang date =
    case lang of
        Portuguese ->
            formatUtc
                Config_pt_br.config
                "%d/%m/%Y"
                date

        _ ->
            formatUtc
                Config_en_us.config
                "%b %-@d, %Y"
                date
