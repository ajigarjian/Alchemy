/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

const colors = require("tailwindcss/colors");

module.exports = {
    
    content: [
        /**
         * HTML. Paths to Django template files that will contain Tailwind CSS classes.
         */

        /*  Templates within theme app (<tailwind_app_name>/templates), e.g. base.html. */
        '../templates/**/*.html',
        
        /*
         * Main templates directory of the project (BASE_DIR/templates).
         * Adjust the following line to match your project structure.
         */
        '../../templates/**/*.html',

        /*
         * Templates in other django apps (BASE_DIR/<any_app_name>/templates).
         * Adjust the following line to match your project structure.
         */
        '../../**/templates/**/*.html',
        './overview.html',

        /**
         * JS: If you use Tailwind CSS in JavaScript, uncomment the following lines and make sure
         * patterns match your project structure.
         */
        /* JS 1: Ignore any JavaScript in node_modules folder. */
        // '!../../**/node_modules',
        /* JS 2: Process all JavaScript files in the project. */
        // '../../**/*.js',

        './node_modules/flowbite/**/*.js',

        /**
         * Python: If you use Tailwind CSS classes in Python, uncomment the following line
         * and make sure the pattern below matches your project structure.
         */
        // '../../**/*.py'
    ],
    variants: {
        extend: {
            textColor: ['group-hover'],
        },
    },
    theme: {
        extend: {
            fontSize: {
                '10xl': '10rem',
                '11xl': '12rem',
                '12xl': '15rem',
                '13xl': '20rem',
            },

            minWidth: {
                '36': '9rem',
                '128': '128px',
                '256': '256px',
                '300': '300px',
                '384': '384px',
                '512': '512px',
                '768': '768px',
            },

            width: {
                '24' : '6rem',
                '128': '32rem',
                '192': '48rem',
                '256': '64rem',
                '320': '80rem',
                '512': '128rem',
            },

            height: {
                '72': '18rem',
                '144': '36rem',
                '168': '42rem',
                '192': '48rem'
            },

            minHeight: {
                '144': '36rem',
                '168': '42rem',
                '192': '48rem',
                '256': '256px',
                '300': '300px',
                '512': '512px',
                '768': '768px',
                '900': '900px',
            },

            gridTemplateColumns: {
                '2': 'repeat(2, minmax(0, 1fr))',
                '4': 'repeat(4, minmax(0, 1fr))',
            },

            backgroundImage: {
                'bg-gradient-to-t': 'background-image: linear-gradient(to top, var(--tw-gradient-stops))',
            },

            colors: {
                blue: colors.blue,
                green: colors.green,
                pink: colors.pink
              }

        },
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/line-clamp'),
        require('@tailwindcss/aspect-ratio'),
        require('flowbite/plugin')({  //added for flowbite css components and ApexCharts
            charts: true,
        }),
    ],
}