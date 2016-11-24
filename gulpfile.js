var gulp = require('gulp');
var elm  = require('gulp-elm');
var uglify = require('gulp-uglify');
var rename = require('gulp-rename');

gulp.task('elm', function () {
  return gulp.src('jarbas/frontend/elm/Main.elm')
    .pipe(elm())
    .pipe(uglify())
    .pipe(rename('jarbas/frontend/static/app.js'))
    .pipe(gulp.dest('.'));
});
