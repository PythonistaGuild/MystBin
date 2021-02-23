import Cookies from "cookies";

export default function DiscordAuth(props) {
  const { status, msg } = props;
  return (
    <div>
      {status}
      {msg}
    </div>
  );
}

export const getServerSideProps = async ({ req, res, query }) => {
  const cookies = new Cookies(req, res);
  const token = cookies.get("auth");

  const resp = await fetch("http://172.25.0.11:9000/users/me", {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });

  return { props: { status: resp.status, msg: resp.statusText } };
};
