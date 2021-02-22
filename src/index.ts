import 'bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

require('expose-loader?exposes=io!socket.io-client');
require('expose-loader?exposes=d3!d3');
require('expose-loader?exposes=analyzer|default!./analyzer');
require('expose-loader?exposes=r6r!./canvas-renderer');
