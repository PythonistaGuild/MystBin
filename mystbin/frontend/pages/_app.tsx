import "../styles/globals.css";
import "bootstrap/dist/css/bootstrap.min.css";
import Script from "next/script";


function MyApp({ Component, pageProps }) {
  return(<>
  <Script async={"async"} src={"https://media.ethicalads.io/media/client/ethicalads.min.js"} strategy={"beforeInteractive"}/>
  <Component {...pageProps} />;
    </>)
}

export default MyApp;
