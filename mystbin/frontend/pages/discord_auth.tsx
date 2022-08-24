import SleeperPush from "../components/Sleeper";
import Cookies from "cookies";
import config from "../config.json";

export default function DiscordAuth(props) {
  const { token } = props;

  return (
    <div>{token ? <SleeperPush ms={0} route={"/success"} /> : "ERROR"}</div>
  );
}

export const getServerSideProps = async ({ req, res, query }) => {
  console.error(1);
  const cookies = new Cookies(req, res);
  let headers;

  if (cookies.get("auth")) {
    headers = {
      "Content-Type": "application/json",
      Authorization: cookies.get("auth"),
    };
  } else {
    headers = {
      "Content-Type": "application/json",
      "User-Agent": "MystBin-FrontEnd",
      "Access-Control-Allow-Origin": "*",
    };
  }
  let response = await fetch(
    `${config["site"]["backend_site"]}/users/connect/discord/`,
    {
      method: "POST",
      headers: headers,
      body: JSON.stringify(query),
    }
  );

  console.error(2);
  const token = await response.json();
  cookies.set("auth", token["token"], { httpOnly: false });
  console.error(3);
  return { props: { token } };
};
