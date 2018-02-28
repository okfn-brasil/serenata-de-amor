module Format.Url exposing (queryEscape, queryPair, url)

import Http exposing (encodeUri)


--
-- Quick replacement for the missing Http.url function
--


{-| Escapes a URL with query parameters:

    url "http://jarbas.dsbr.com/" [ ( "format", "json" ), ( "another", "foo bar" ) ]
    --> "http://jarbas.dsbr.com/?format=json&another=foo+bar"

-}
url : String -> List ( String, String ) -> String
url baseUrl args =
    case args of
        [] ->
            baseUrl

        _ ->
            baseUrl ++ "?" ++ String.join "&" (List.map queryPair args)


{-| Generates an encoded URL parameter:

    queryPair ( "another", "foo bar" ) --> "another=foo+bar"

-}
queryPair : ( String, String ) -> String
queryPair ( key, value ) =
    queryEscape key ++ "=" ++ queryEscape value


{-| Generates an encoded URL value:

    queryEscape "foo bar" --> "foo+bar"

-}
queryEscape : String -> String
queryEscape string =
    string
        |> encodeUri
        |> String.split "%20"
        |> String.join "+"
