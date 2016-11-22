module Tests exposing (..)

import Test exposing (..)
import Expect
import Documents.Update exposing (..)


all : Test
all =
    describe "Documents"
        [ test "Documents.totalPages" <|
            \() ->
                Expect.equal (Documents.Update.totalPages 20) 3
        , test "Documents.onlyDigits" <|
            \() ->
                Expect.equal (Documents.Update.onlyDigits "12a3") "123"
        ]
