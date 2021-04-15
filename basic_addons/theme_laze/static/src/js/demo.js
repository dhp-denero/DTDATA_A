jQuery(document).ready(function($) {
    if( $('section').hasClass('as-home-slider') === true ) 
    {
     $('body').addClass('header-op-0');
    }

    if( $('section').hasClass('as-home-slider01') === true ) 
    {
     $('body').addClass('header-op-2');
    }

    if( $('section').hasClass('as-home-slider-cr') === true ) 
    {
     $('body').addClass('header-op-1'); // Done //
    }

    if( $('section').hasClass('as-home-banner') === true ) 
    {
     $('body').addClass('header-op-3'); // Done //
    }

    if( $('section').hasClass('as-animated-slider') === true ) 
    {
     $('body').addClass('header-op-4');
    }

    if( $('section').hasClass('as-home-slider02') === true ) 
    {
     $('body').addClass('header-op-5');
    }

});