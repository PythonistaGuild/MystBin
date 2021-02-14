import Head from "next/head";
import dynamic from "next/dynamic";
import Base from "../components/Base";
import styles from "../styles/Home.module.css";
import { PropsWithoutRef } from "react";
import { GetServerSideProps } from "next";

const PostMonacoEditor = dynamic(() => import("../components/EditorTabs"), {
  ssr: false,
});

export default function Paste(props: PropsWithoutRef<{ paste }>) {
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
        <title key="pasteTitle">MystBin - {paste['pid']}</title>
        <meta property="og:title" content={`MystBin - ${paste["pid"]}`} key="pasteTitleOg"/>
        <meta property="og:description" content={`This paste has (${paste["pastes"].length}) attached and expires in 2 hours.`} key="pasteDesc"/>
        <meta property="og:image" content={"https://i.imgur.com/6aYhtEf.png"} key="pasteLogo"/>
        <meta property="og:url" content={"https://staging.mystb.in/" + paste["pid"]} key="pasteUrl"/>

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
  console.log('SERVER')
  const API = "http://api:9000";
  console.log(1)
  const { pid } = query;
  const response = await fetch(`${API}/paste/${pid}`);
  console.log(1)

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
