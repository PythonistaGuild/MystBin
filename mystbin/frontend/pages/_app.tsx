import "../styles/globals.css";
import "bootstrap/dist/css/bootstrap.min.css";
import Script from "next/script";


function MyApp({ Component, pageProps }) {
  return(<>
  <script async src={"https://media.ethicalads.io/media/client/ethicalads.min.js"}/>
  <Component {...pageProps} />;
    </>)
}

export default MyApp;
