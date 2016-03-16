angular.module('hierarchie')
  .config(['$routeProvider',
    function($routeProvider) {
      $routeProvider.when('/', {
        templateUrl: 'views/charts.html',
        controller: 'MainCtrl'
      })
        .when('/fcc', {
          templateUrl: 'views/fcc.html',
          controller: 'FccCtrl'
        })
        .when('/about', {
          templateUrl: 'views/about.html'
        })
        .otherwise({
          redirectTo: '/'
        });
    }
  ]);
