module Reimbursement.Company.Update exposing (..)

import Char
import Format.Url exposing (url)
import Http
import Material
import Reimbursement.Company.Decoder exposing (decoder)
import Reimbursement.Company.Model exposing (Company, Model)
import String


type Msg
    = LoadCompany (Result Http.Error Company)
    | Mdl (Material.Msg Msg)


{-| Cleans up a CNPJ field allowing numbers only:

    cleanUp (Just "12.345.678/9012-34") --> "12345678901234"

-}
cleanUp : Maybe String -> String
cleanUp cnpj =
    cnpj
        |> Maybe.withDefault ""
        |> String.filter Char.isDigit


{-| CNPJ validator:

    isValid (Just "12.345.678/9012-34") --> True

    isValid (Just "12345678901234") --> True

    isValid (Just "123.456.789-01") --> False

    isValid Nothing --> False

-}
isValid : Maybe String -> Bool
isValid cnpj =
    if String.length (cleanUp cnpj) == 14 then
        True
    else
        False


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadCompany (Ok company) ->
            ( { model | company = Just company, loading = False, loaded = True }, Cmd.none )

        LoadCompany (Err error) ->
            let
                err =
                    Debug.log "ApiError" (toString error)
            in
                ( { model | loaded = True, error = Just error }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


load : Maybe String -> Cmd Msg
load cnpj =
    if isValid cnpj then
        let
            path : String
            path =
                String.concat
                    [ "/api/company/"
                    , cleanUp cnpj
                    , "/"
                    ]

            query : List ( String, String )
            query =
                [ ( "format", "json" ) ]
        in
            decoder
                |> Http.get (url path query)
                |> Http.send LoadCompany
    else
        Cmd.none
