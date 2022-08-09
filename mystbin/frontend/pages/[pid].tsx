import dynamic from "next/dynamic";
import Base from "../components/Base";
import styles from "../styles/Home.module.css";
import { PropsWithoutRef } from "react";
import { GetServerSideProps } from "next";
import Head from "next/head";

import config from "../config.json";

const PostMonacoEditor = dynamic(() => import("../components/EditorTabs"), {
  ssr: false,
});

export default function Pastey(props: PropsWithoutRef<{ paste }>) {
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
        <title key="pasteTitle">MystBin - {paste["pid"]}</title>
        <meta
          property="og:title"
          content={`MystBin - ${paste["pid"]}`}
          key="pasteTitleOg"
        />
        <meta
          property="og:description"
          content={paste.status !== 401 ? `This paste has (${paste["pastes"].length}) attached file(s)` : "This paste is password protected."}
          key="pasteDesc"
        />
        <meta
          property="og:image"
          content={"https://i.imgur.com/6aYhtEf.png"}
          key="pasteLogo"
        />
        <meta
          property="og:url"
          content={`${config.site.frontend_site}/${paste["pid"]}`}
          key="pasteUrl"
        />
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
  const { pid } = query;
  const response = await fetch(
    `${config["site"]["backend_site"]}/paste/${pid}`
  );

  if (response.status === 404) {
    return {
      notFound: true,
    };
  }

  let paste = await response.json();
  paste["status"] = response.status;
  paste["pid"] = pid;

  return {
    props: { paste },
  };
};
