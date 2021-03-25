import SleeperPush from "../components/Sleeper";
import Cookies from "cookies";
import config from "../config.json";

export default function GoogleAuth(props) {
  const { token } = props;

  return (
    <div>{token ? <SleeperPush ms={0} route={"/success"} /> : "ERROR"}</div>
  );
}

export const getServerSideProps = async ({ req, res, query }) => {
  let response = await fetch(`${config["app"]["backend_site"]}/users/connect/google/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });

  const token = await response.json();
  const cookies = new Cookies(req, res);
  cookies.set("auth", token["token"], { httpOnly: false });

  return { props: { token } };
};
