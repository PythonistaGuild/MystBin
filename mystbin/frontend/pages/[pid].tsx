import Head from "next/head";
import dynamic from "next/dynamic";
import Base from "../components/Base";
import styles from "../styles/Home.module.css";
import { PropsWithoutRef } from "react";
import { GetServerSideProps } from "next";

const PostMonacoEditor = dynamic(() => import("../components/EditorTabs"), {
  ssr: false,
});

export default function Home(props: PropsWithoutRef<{ paste }>) {
  const { paste } = props;
  let initialData = [];

  if (paste["status"] === 401) {
    initialData.push({
      title: "PASSWORD PROTECTED",
      content: "This is a password protected paste.",
    });
  } else {
    for (let file of paste["pastes"]) {
      initialData.push({ title: file["filename"], content: file["content"] });
    }
  }

  return (
    <div>
      <Head>
        <title>MystBin</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Base className={styles.Tabs}>
        <PostMonacoEditor
          initialData={initialData}
          hasPassword={paste["status"] === 401}
          pid={paste["pid"]}
        />
      </Base>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps = async ({ query }) => {
  const API = "https://api-staging.mystb.in";

  const { pid } = query;
  const response = await fetch(`${API}/paste/${pid}`);

  if (response.status === 404) {
    console.log("Invalid Paste");
  }

  let paste = await response.json();
  paste["status"] = response.status;
  paste["pid"] = pid;

  return {
    props: { paste },
  };
};
