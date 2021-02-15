import SleeperPush from "../components/Sleeper";
import { setCookie } from "nookies";

export default function DiscordAuth(props) {
  const { token } = props;
  return (
    <div>
      {token ? setCookie(null, "state", "true", { path: "/" }) : null}
      {token ? <SleeperPush ms={0} route={"/success"} /> : "ERROR"}
    </div>
  );
}

export const getServerSideProps = async ({ query, ctx }) => {
  let response = await fetch("http://api:9000/users/connect/discord/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });

  const token = await response.json();
  setCookie(ctx, "auth", token, { httpOnly: true, path: "/" });

  return { props: { token } };
};
